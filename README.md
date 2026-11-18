<a href="https://dortort.com"><img src="assets/hero.svg" width="100%" alt="Francis Eytan Dortort, Senior DevSecOps Engineer and Cloud Solutions Architect"></a>

I started as a full-stack developer and have spent 20 years growing into cloud architecture and DevSecOps. I design multi-account AWS platforms, build them with Terraform and Kubernetes, and keep them PCI-DSS and SOC 2 compliant. CCSP certified.

**[Blog](https://dortort.com)** &nbsp;&nbsp; **[CV](https://dortort.com/cv/)**

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/section-open-source-dark.svg">
  <img src="assets/section-open-source-light.svg" width="100%" alt="Open source">
</picture>

<a href="https://github.com/stackorder/stackorder">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/stackorder-dark.svg">
    <img src="assets/stackorder-light.svg" width="100%" alt="Stackorder: five stacks applied in three dependency waves">
  </picture>
</a>

Which stacks, in what order. Stackorder plans every Terraform or OpenTofu stack a pull request affects and applies them in dependency waves on your own GitHub Actions runners. Its server stores no state, and holds no cloud credentials unless you turn on shared outputs.

**[stackorder.io](https://stackorder.io)** &nbsp;&nbsp; **[Docs](https://docs.stackorder.io)** &nbsp;&nbsp; **[Source](https://github.com/stackorder/stackorder)**

<a href="https://github.com/dortort/wawarden">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/wawarden-dark.svg">
    <img src="assets/wawarden-light.svg" width="100%" alt="WaWarden: messages from allowlisted chats reach your agent, the rest stop at the gate">
  </picture>
</a>

A self-hosted WhatsApp gateway for your own AI agents. WaWarden links one personal account, keeps its messages in a local archive, and exposes them over REST and MCP. Each client gets a token that reads only the chats on its allowlist.

**[Docs](https://wawarden.dortort.dev/)** &nbsp;&nbsp; **[Source](https://github.com/dortort/wawarden)**

<a href="https://github.com/dortort/claude-plugins/tree/main/plugins/taint-guard">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/taintguard-dark.svg">
    <img src="assets/taintguard-light.svg" width="100%" alt="TaintGuard in a Claude Code session: after Read(.env) the session carries the label secret, and WebFetch and Bash are refused">
  </picture>
</a>

A Claude Code mod that remembers which sensitive or untrusted sources have entered a session and refuses risky tool calls once they have. After Claude reads an `.env` file, `Bash`, `WebFetch` and outbound MCP tools are refused outright.

**[Source](https://github.com/dortort/claude-plugins/tree/main/plugins/taint-guard)** &nbsp;&nbsp; **[Why agent permissions need history](https://dortort.com/posts/safe-tools-unsafe-session-why-agent-permissions-need-history/)**

<a href="https://github.com/dortort/across-amazon">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/across-amazon-dark.svg">
    <img src="assets/across-amazon-light.svg" width="100%" alt="Across Amazon: four Amazon stores ranked by item, shipping and import fees, lowest delivered total first">
  </picture>
</a>

A Chrome extension that finds the Amazon store that delivers a product to you for the lowest total: item, shipping and import fees.

**[Chrome Web Store](https://chromewebstore.google.com/detail/across-amazon/jipkoghidlgfmgoihpaecdnaapiniglc)** &nbsp;&nbsp; **[Website](https://across-amazon.dortort.dev)** &nbsp;&nbsp; **[Source](https://github.com/dortort/across-amazon)**

<details>
<summary>More open-source projects</summary>
<br>

<!-- CURRENT_PROJECTS_START -->
- [agent-bound](https://github.com/dortort/agent-bound) — Access control framework for MCP servers with Android-style permissions.
- [agentry](https://github.com/dortort/agentry) — Playwright for AI Agents — end-to-end testing for agent CLIs, MCP servers, and skills. Drive a real agent, assert on what it did, replay deterministically in CI.
- [ai-tool-guard](https://github.com/dortort/ai-tool-guard) — Policy enforcement middleware for AI SDK tool calls — guards, approvals, rate limiting, and observability.
- [betterleaks-action](https://github.com/dortort/betterleaks-action) — GitHub Action for Betterleaks secrets detection - scan for exposed credentials in your CI/CD pipeline.
- [dgossgen](https://github.com/dortort/dgossgen) — Generate dgoss container test suites from Dockerfiles via static analysis.
- [gemini-actions](https://github.com/dortort/gemini-actions) — A collection of GitHub Actions powered by Google Gemini that automate repository workflows.
- [keystone](https://github.com/dortort/keystone) — Open-source Electron app for AI-assisted software architecture (PRDs, TDDs, ADRs).
- [moovit-client](https://github.com/dortort/moovit-client) — TypeScript client library for Moovit public transit API (route planning, real-time arrivals, and location search).
- [openclaw-aws](https://github.com/dortort/openclaw-aws) — Infrastructure and deployment automation for OpenClaw on AWS.
- [openclaw-mailguard](https://github.com/dortort/openclaw-mailguard) — OpenClaw plugin for email prompt-injection mitigation with gated tool access.
- [skills](https://github.com/dortort/skills) — Reusable agent skills for AI tools.
- [TADBench](https://github.com/dortort/TADBench) — A unified benchmark for embedding-based threat detection in LLM prompts.
- [terraform-aws-mcpgateway](https://github.com/dortort/terraform-aws-mcpgateway) — Terraform module to deploy MCP Context Forge on AWS — ECS/EKS, Fargate/EC2, Aurora/MySQL, Redis, ALB+WAF.
<!-- CURRENT_PROJECTS_END -->

</details>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/section-writing-dark.svg">
  <img src="assets/section-writing-light.svg" width="100%" alt="Writing">
</picture>

<!-- LATEST_WRITING_START -->
<sub>November 5, 2026</sub><br>
**[Safe Tools, Unsafe Session: Why Agent Permissions Need History](https://dortort.com/posts/safe-tools-unsafe-session-why-agent-permissions-need-history/)**<br>
Taint tracking for AI agent tool calls: per-tool allow/deny rules miss the lethal trifecta, so TaintGuard gates Claude Code by what the session has read.

<sub>August 2, 2026</sub><br>
**[Agentic DevOps Security: Old IAM Failures at New Speed](https://dortort.com/posts/agentic-devops-security-old-iam-failures-at-new-speed/)**<br>
Agentic DevOps security concerns aren't new — they're old IAM failures (least privilege, step-up auth, JIT) agents now exercise at machine speed.

<sub>May 20, 2026</sub><br>
**[Monorepo vs Multi-Repo: Why AI Agents Tip the Scale](https://dortort.com/posts/monorepo-vs-multi-repo-why-ai-agents-tip-the-scale/)**<br>
AI coding agents optimize for full-codebase context, atomic changes, and connected dependency graphs — properties that monorepo provides by default.

<sub>April 7, 2026</sub><br>
**[Closing the automation gap in Claude Code](https://dortort.com/posts/closing-the-automation-gap-in-claude-code/)**<br>
claude-code-scheduler bridges Claude Code to launchd and crontab for persistent, observable, stateful task automation — no Desktop app required.
<!-- LATEST_WRITING_END -->

<details>
<summary>Earlier articles</summary>
<br>

<!-- EARLIER_WRITING_START -->
- [Beyond terraform_remote_state: five ways to share data across Terraform configurations](https://dortort.com/posts/beyond-terraform-remote-state-five-ways-to-share-data-across-configurations/) <sub>March 9, 2026</sub>
- [Don't Ditch AGENTS.md — Fix What's In It](https://dortort.com/posts/dont-ditch-agents-md-fix-whats-in-it/) <sub>February 24, 2026</sub>
- [Agentic AI is reintroducing ClickOps](https://dortort.com/posts/agentic-operations-clickops/) <sub>February 21, 2026</sub>
- [dgoss: Testing the Container, Not Just the Image](https://dortort.com/posts/runtime-contract-tests-with-dgoss/) <sub>January 8, 2026</sub>
- [A Practical Guide to Terraform Dependency Management](https://dortort.com/posts/terraform-version-constraints/) <sub>August 4, 2025</sub>
- [Stop Scripting, Start Architecting: The OOP Approach to Terraform](https://dortort.com/posts/stop-scripting-start-architecting-terraform-oop/) <sub>July 2, 2025</sub>
- [Why GitFlow Fails at Infrastructure](https://dortort.com/posts/terraform-strategy-gitflow-vs-trunk-based/) <sub>June 4, 2025</sub>
- [Modernizing Scheduled Tasks: Reliability, Scale, and Zero Maintenance](https://dortort.com/posts/building-serverless-cron-on-aws/) <sub>May 6, 2025</sub>
- [How Serverless Shrinks PCI Scope](https://dortort.com/posts/serverless-pci-dss-scope-reduction/) <sub>April 3, 2025</sub>
- [Terraform at Scale: Folders, Workspaces, or Services?](https://dortort.com/posts/structuring-terraform-for-multi-environment-microservice-architectures/) <sub>March 4, 2025</sub>
- [Kubernetes vs. Proprietary Container Services: A Technical and Pragmatic Comparison](https://dortort.com/posts/kubernetes-vs-proprietary-container-services/) <sub>February 10, 2025</sub>
- [Idempotent Dockerfiles: Desirable Ideal or Misplaced Objective?](https://dortort.com/posts/idempotent-dockerfiles/) <sub>January 15, 2025</sub>
<!-- EARLIER_WRITING_END -->

</details>

**[All articles at dortort.com](https://dortort.com)**
