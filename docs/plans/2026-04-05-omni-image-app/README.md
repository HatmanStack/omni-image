# Omni Image -- Chat-based Image Generation with Nova 2 Omni

## Overview

Omni Image is a chat-based image generation application powered by Amazon Nova 2 Omni.
Users interact through natural language -- typing prompts and optionally uploading images --
to generate and edit images via a conversational flow. The app displays generated images
prominently in chat bubbles with model text as captions below.

The architecture is a monorepo with a SvelteKit static frontend deployed on AWS Amplify and a
single Python Lambda function behind API Gateway that proxies Bedrock Converse API calls. The
Lambda also handles S3 storage (inputs and outputs) and S3-backed rate limiting. This replaces
the containerized Gradio + Lambda deployment pattern from canvas-demo with a lighter, more
maintainable stack.

This is a separate portfolio piece from canvas-demo (which stays live as-is). The backend
follows the same quality bar and patterns as canvas-demo (singleton AWS clients, dataclass
config, custom exception hierarchy, CloudWatch logging, S3-backed rate limiting). The frontend
follows SvelteKit conventions from sv-portfolio. The deploy script follows the interactive
SAM-based pattern from savorswipe.

## Prerequisites

- **Python >= 3.11** with **uv** for package management
- **Node.js >= 20** with **pnpm** for frontend package management
- **AWS SAM CLI** for backend deployment
- **AWS CLI** configured with credentials that have Bedrock, S3, Lambda, API Gateway access
- **Nova 2 Omni model access** (`us.amazon.nova-2-omni-v1:0`) enabled in us-west-2
- **Git** for version control

## Phase Summary

| Phase | Goal | Token Estimate |
|-------|------|----------------|
| 0 | Foundation -- architecture decisions, tech stack, testing strategy, shared patterns | ~3,000 |
| 1 | Backend -- Lambda function, Bedrock Converse API, rate limiter, S3 storage, SAM template, deploy script, backend CI | ~45,000 |
| 2 | Frontend -- SvelteKit chat UI, API client, message display, image upload, settings panel, Amplify config, frontend CI | ~42,000 |

## Navigation

- [Phase-0.md](Phase-0.md) -- Foundation (architecture, stack, conventions)
- [Phase-1.md](Phase-1.md) -- Backend implementation
- [Phase-2.md](Phase-2.md) -- Frontend implementation
- [feedback.md](feedback.md) -- Review feedback tracking
