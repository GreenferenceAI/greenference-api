# HuggingFace Token — Custom Model Deploy Test Plan

Manual end-to-end test scenarios for the user-supplied HF token path on
`/models` → "Deploy custom model".

## Background

Two ways an HF token can reach the inference container:

1. **User-supplied** at deploy time (the new path). UI field on `/models`
   → `WorkloadCreateRequest.metadata.hf_token` → `workload.metadata` on
   control-plane → `artifact.payload["hf_token"]` on the miner →
   `docker run -e HF_TOKEN=…`.
2. **Miner operator's env**. Falls back to `HF_TOKEN` /
   `HUGGING_FACE_HUB_TOKEN` exported in the node-agent process env.

User token wins when both exist.

## Verifying env injection inside the container

Run on the miner host:

```bash
docker inspect $(docker ps --filter "name=greencompute-inf-" -q | head -1) \
  | grep -A1 "HF_TOKEN\|HUGGING_FACE_HUB_TOKEN"
```

---

## Scenario 1 — Public small model, no token (control)

- **Model**: `Qwen/Qwen2.5-0.5B-Instruct`
- **HF token field**: blank
- **Expected**: deploys in ~30–90 s. `/v1/chat/completions` returns 200.
- **Purpose**: regression check — confirms the no-token path still works.

## Scenario 2 — Public mid-size, no token

- **Model**: `mistralai/Mistral-7B-Instruct-v0.3` (≥16 GB VRAM) or
  `meta-llama/Llama-3.2-1B-Instruct`
- **HF token field**: blank
- **Expected**: pulls without auth, vLLM loads, inference works.

## Scenario 3 — Gated model with USER token (the new path)

- **Model**: `meta-llama/Llama-3.1-8B-Instruct`
- **HF token field**: paste a valid `hf_…` token from an account that has
  accepted the Llama license on huggingface.co.
- **Expected**:
  - Detection panel shows the orange "Required — gated model" pill.
  - Deploy succeeds.
  - `docker inspect` shows `HF_TOKEN=hf_…` in the container env.
- **Purpose**: core new behaviour — user-supplied creds reach the container.

## Scenario 4 — Gated model with WRONG/EXPIRED token (error UX)

- **Model**: `meta-llama/Llama-3.1-8B-Instruct`
- **HF token field**: `hf_invalid_xxx`
- **Expected**: container starts but vLLM exits with 401/403 from HF.
  Deployment flips to `FAILED`; `last_error` reflects HF auth failure.
- **Purpose**: confirms bad tokens fail loudly instead of hanging.

## Scenario 5 — Gated model with MINER token, no user token (fallback)

- **Precondition**: SSH into miner, `export HF_TOKEN=hf_minerops_token`
  in the node-agent env, restart node-agent.
- **Model**: `meta-llama/Llama-3.1-8B-Instruct`
- **HF token field**: blank
- **Expected**: deploys using the miner's env token. Container `HF_TOKEN`
  matches the miner operator's value.
- **Purpose**: verifies fallback didn't regress.

## Scenario 6 — Both tokens present (precedence)

- **Precondition**: miner has `HF_TOKEN=hf_miner_xxx` exported.
- **Model**: `meta-llama/Llama-3.1-8B-Instruct`
- **HF token field**: a different valid `hf_user_yyy`.
- **Expected**: container env shows the **user's** token, not the
  miner's.
- **Purpose**: validates user-wins-over-miner precedence.

## Scenario 7 — Private user-owned repo

- **Model**: a private repo owned by the testing user
  (e.g. `<your-hf-username>/private-test-model`).
- **HF token field**: user's read token for that repo.
- **Precondition**: miner has **no** access to this repo (different
  account / no token / wrong scope).
- **Expected**: deploy succeeds despite the miner never having seen the
  repo.
- **Purpose**: the most differentiating use case — proves any miner can
  serve any user's private model without coordinating creds.

## Scenario 8 — Vision model (multimodal path)

- **Model**: `Qwen/Qwen2-VL-2B-Instruct` (public)
- **HF token field**: blank
- **Template detection**: should flip to `vllm-vision`.
- **Expected**: deploys with `--max-model-len 16384`; multimodal chat
  with one image works.
- **Purpose**: confirms the vision template carries `metadata` through.

## Scenario 9 — Diffusion model

- **Model**: `stabilityai/sdxl-turbo` or `stabilityai/stable-diffusion-2-1`
- **HF token field**: blank
- **Template**: `diffusion`
- **Expected**: diffusion container starts, generates an image.
- **Purpose**: confirms the diffusion template carries `metadata` through.

## Scenario 10 — Featured-model deploy (regression)

- Pick any model from the featured grid on `/models` and click Deploy.
- **HF token field**: blank
- **Expected**: deploys identically to the pre-change behaviour.
- **Purpose**: catches accidental coupling between the new HF field and
  the featured-pickup flow.

---

## Reset between runs

```bash
# UI: terminate each active deployment from /deployments
# or via API:
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$GATEWAY/platform/deployments/<deployment_id>"
```
