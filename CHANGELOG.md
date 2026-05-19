# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog retrospectively consolidates the repository's noisy early AI-assisted history
into meaningful release milestones. Historical tags `b0.9` and `b0.91` are treated as
pre-release markers for the `0.9.x` stabilization phase.

## [Unreleased]

### Added
- Ongoing changes should continue to use Conventional Commits so `feat` maps to `MINOR`,
  `fix` maps to `PATCH`, and `feat!` or `BREAKING CHANGE` maps to `MAJOR`.

### Changed
- `VERSION`, `CHANGELOG.md`, and the release workflow are now the authoritative release inputs.

## [1.0.0] - 2026-05-19

First structured stable release of KickerKasse after retrospective history consolidation and
release-governance hardening.

### Added
- Root `VERSION` file for a single repository-wide release number.
- Release workflow with Conventional-Commit validation, SemVer checks, frontend build output,
  and GitHub release bundle creation.
- Repository-level release guidance for changelog discipline, tag naming, and meaningful commits.

### Changed
- Consolidated 352 historical commits and 75 pull requests into semantically versioned milestones.
- Formalized the repository around reproducible release inputs instead of ad-hoc beta tags.

## [0.9.2] - 2026-05-19

Release-candidate stabilization phase that made the admin area operationally consistent and
prepared the repository for a production-grade release. Historical tag alignment: `b0.91`.

### Added
- Donation link and deployment-oriented README sections.
- Responsive modal variants and compact admin layouts for smaller displays.
- Unified `AdminConfig` area by combining design, data maintenance, and extended settings.
- Sticky admin headers and consistent inactive-tab styling across admin pages.

### Changed
- Moved non-operational and design-heavy reference material into `.github/development-documentation`.
- Standardized admin layouts, buttons, spacing, and navigation behavior across views.

### Fixed
- Finance and correction scroll/header offset issues.
- Product card width regressions and modal sizing inconsistencies.
- `.env.example` scheduler entry cleanup and repository cleanup for uploaded sample assets.

## [0.9.1] - 2026-05-06

Correctness and security hardening phase centered on correction bookings, permissions, and session handling.

### Added
- Configurable session timer for controlled auto-logout behavior.
- Admin correction tab with mandatory reasons for account/product corrections.
- Finance integration for correction bookings and correction visibility in operational views.

### Changed
- Tightened role permission boundaries and documented the updated authorization model.

### Fixed
- Extended-settings authorization guard ordering.
- Correction validation wording and finance integration polish.

## [0.9.0] - 2026-05-04

Feature-complete beta for the point-of-sale experience, with layout variants, image tooling, and
frontend architecture cleanup. Historical tag alignment: `b0.9`.

### Added
- Admin search filters and stricter cart stock handling.
- Product `Warengruppe` metadata and Z-Bon aggregation by product group.
- HTML preview layouts for checkout and receipt designs.
- Multiple Kasse layout variants, category color styling, and business-data design controls.
- Interactive product image crop editor with Kasse card preview and pan/zoom controls.
- Variable pricing, tip/donation handling, and reset-to-original image behavior.
- PWA icon set improvements including maskable app icons.

### Changed
- Extracted shared Kasse behavior into a reusable `useKasse` composable.
- Added synchronized `kasse_layout` settings across clients and settings screens.

### Fixed
- Layout persistence and cross-client layout synchronization.
- Crop bounds, scale handling, and image preview regressions.

## [0.8.0] - 2026-04-27

Operational hardening milestone focused on admin workflows, cash/booking correctness, and reset safety.

### Added
- Internal material-sale context and refined finance views for internal accounts.
- Open-Deckel indicators and unlimited-stock product handling.
- Hard-reset flow with sequence reset and controlled logout behavior.
- Tabular finance views, voucher sections in finance, and explicit withdrawal payment handling.

### Changed
- Redesigned admin edit modals and aligned admin layouts with the members view.
- Clarified booking, audit, and payment labeling inside finance and Z-Bon flows.

### Fixed
- Booking audit calculations, transaction sorting, and recharge vs. cash separation.
- Hard-reset cleanup for linked users and category recreation defaults.
- Scheduler/admin view accessibility and action button semantics.

## [0.7.0] - 2026-04-24

Breaking domain-model expansion that renamed stored-value concepts and introduced deeper finance workflows.

### Added
- Verzehrkarten as a first-class prepaid flow with updated voucher and checkout behavior.
- Material-account and Deckel workflows in checkout and finance areas.
- Richer finance modals, bon-button adjustments, and improved cashier/admin UI states.
- Project branding under the name **KickerKasse by KGB Hannover**.

### Changed
- Renamed the former Guthabenkarten concept to Verzehrkarten across backend, database, and UI.
- Refined admin/cashier frontend flows and account views.

### Fixed
- Backend startup import errors and migration defaults around the evolving finance model.
- Product deletion wiring and Z-Bon modal state handling.

## [0.6.0] - 2026-04-21

Administrative and operational maturity milestone covering user lifecycle, finance workflows, and deployability.

### Added
- Member metadata, finance modal groundwork, and club-account handling.
- Top-admin backend maintenance flow and password-oriented user-management improvements.
- Soft-delete support for users and better gift-voucher attribution.
- Frontend lockfile to stabilize deployments and builds.

### Changed
- Tightened user/role flows, finance naming, and Z-Bon operator selection.

### Fixed
- Voucher club-account routing and user deletion edge cases.
- Deployment stack reproducibility issues caused by missing frontend lock metadata.

## [0.5.0] - 2026-04-19

Identity and experience milestone that established roles, membership workflows, and installable app branding.

### Added
- Role-based safeguards for critical actions.
- Configurable app title, theme handling, and contrast helpers.
- Membership improvements including sequential member numbers and optional email flows.

### Changed
- Finalized branding and validation behavior for the PWA-facing frontend.

### Fixed
- Member-number backfill ordering and retry handling.

## [0.4.0] - 2026-04-17

Voucher stabilization milestone that connected voucher lifecycle handling with Z-Bon and finance workflows.

### Added
- Admin voucher editing, improved redemption handling, and clearer finance/Z-Bon voucher flows.
- Better Z-Bon preview feedback and cash-count display refinements.

### Changed
- Simplified voucher models and enum migration behavior.
- Aligned voucher API, UI, and generated voucher-code handling.

### Fixed
- Voucher creation, listing, redemption, and validation feedback defects from the initial rollout.

## [0.3.0] - 2026-04-15

First voucher implementation spike. This introduced major domain functionality, but the feature was still unstable.

### Added
- Initial voucher issuance and integration into the wider checkout flow.

### Fixed
- Rapid same-day routing, database, and voucher hotfixes that followed the first rollout.

## [0.2.0] - 2026-04-14

Early product milestone that established the Z-Bon as the financial reporting core and pivoted report output to HTML.

### Added
- First Z-Bon implementation, including detailed views and export rendering.
- Category and counter updates plus broader functional monitoring hooks.

### Changed
- Switched the Z-Bon output approach away from PDF and toward HTML rendering.
- Applied broader CSS and layout passes while the finance flow was still forming.

### Fixed
- HTML API integration errors discovered during the rendering pivot.

## [0.1.0] - 2026-04-12

Initial development baseline and bootstrap phase.

### Added
- First repository import with backend, frontend, and Docker-based local startup.

### Changed
- Updated API routing and Docker port mapping during the first deployment attempts.

### Fixed
- Initial login fixes and early Docker/Windows compatibility fixes.
