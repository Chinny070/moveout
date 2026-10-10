# MoveOut Frontend Deployment

## Release status

This document describes the reviewed Vite frontend deployment setup. The website has not yet been deployed to Vercel. Public URL, Vercel project name, and deployed commit are pending successful hosting setup and production verification.

- GitHub repository: <https://github.com/Chinny070/moveout>
- Branch: `main`
- Frontend release commit pushed to `origin/main`: `2cc297f9f8517863f4eb30d2a45fd567e42e5c53`
- Vercel project: not linked in this checkout (`.vercel/project.json` is absent)
- Production URL: pending

## Build configuration

Vercel should detect Vite from `package.json` and use:

- Install: `npm install` (or the platform's lockfile-aware equivalent)
- Build: `npm run build`
- Output directory: `dist`
- Environment variables: none required

The application uses hash-based screen links (`/#properties`, `/#inspections`, and similar), so direct screen links and refreshes are served from the static root without a server-side SPA rewrite. The client stores Demo Mode inspections and photographs in browser IndexedDB; this data is not part of the build artifact. StudioNet reads use the public StudioNet RPC and the deployed contract address below. No private wallet values or API keys are embedded in the frontend. The SDK bundle includes its unused Localnet chain definition with a localhost endpoint, while MoveOut constructs the active client with the explicit public StudioNet endpoint; the application source has no localhost RPC dependency.

## StudioNet

- Network: GenLayer StudioNet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Contract: `0x4F96B354b19541F7087b73c548Dc2db380e09b77`
- AI-dependent methods remain disabled in the frontend write allowlist.
- No contract changes or blockchain writes are part of frontend deployment.

The RPC and contract address are public application configuration, not secrets. A browser wallet is requested only after an explicit user action. Wallet approval and write transaction completion must be tested by the owner in a compatible browser wallet; this environment has not performed a wallet signature.

## Plan eligibility and deployment gate

Vercel's [Hobby plan](https://vercel.com/docs/plans/hobby) is free but restricted to personal, non-commercial use. MoveOut is a property-inspection application intended for property managers and tenants, so Hobby eligibility must be confirmed against the actual intended use before creating or deploying a Vercel project. No paid plan, billing activation, or custom domain is authorized. If the intended use is commercial, do not deploy under Hobby; deployment requires a separately approved eligible $0 hosting option or an explicit budget decision.

Vercel CLI is installed locally, but account identity and linked-project status have not been verified because the CLI identity request timed out in this environment. No Vercel project or deployment was created.

## Redeployment procedure

After plan eligibility and account access are confirmed:

1. Connect `Chinny070/moveout` to an eligible Vercel project or use the official Vercel CLI login flow.
2. Verify project settings are `npm run build` and `dist`; no environment variables are needed.
3. Create a preview deployment first and check its public URL before production promotion.
4. Verify the homepage, Demo Mode persistence, hash-linked views, StudioNet read-only behavior, and mobile/desktop layouts on the hosted domain.
5. Only after a successful preview, create the production deployment using the approved Git integration or CLI. Do not make StudioNet write calls during deployment verification.

## Verification record

Local production build and frontend tests pass for the release candidate. The Python contract regression suite also passes locally. These results do not constitute Vercel deployment verification. Production browser checks, hosted StudioNet read-only checks, and public HTTPS wallet detection remain pending because no production deployment exists.
