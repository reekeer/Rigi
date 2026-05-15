# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.




## [dev] - 2026-05-15

### Changed

- **README:** remove info about pypi ([`bb31f1d`](https://github.com/reekeer/Rigi/commit/bb31f1dd2d8aff4f983201f72874fa6a03ff004d))

### Changed

- bump 1.3.3 ([`50f6b68`](https://github.com/reekeer/Rigi/commit/50f6b687e95b9464fd9d6541ea89e8b7be648328))

### Changed

- add build and release to pypi ([`3b57fda`](https://github.com/reekeer/Rigi/commit/3b57fda734f1acbeb8465f7c177550112d5980a9))
- remove verify in workflow ([`5ffb40f`](https://github.com/reekeer/Rigi/commit/5ffb40f4ac18652c03d0b0850370a3c1a51c9e0d))

### Changed

- **pyproject:** rename project for pypi ([`ffa708b`](https://github.com/reekeer/Rigi/commit/ffa708b4405cbca3f63fbd9304bb06b0832f69fa))



## [dev] - 2026-05-15

### Added

- replace Switch with custom Checkbox (☐/☑) and draggable Slider+Input for settings ([`0847b58`](https://github.com/reekeer/Rigi/commit/0847b58710703e486ae74c91e249f0cf5c88f02e))

### Fixed

- correct StatusBarItem CSS selector, add StatusBar width, fix Screen overflow, fix terminal history background, remove dock from NotificationRack ([`d276050`](https://github.com/reekeer/Rigi/commit/d2760501e54cfa61c5e7404b4e9ae3feb42d12aa))
- defer settings category mount with call_after_refresh to prevent crash on tab click ([`dcf177c`](https://github.com/reekeer/Rigi/commit/dcf177c2b1dafa805d7c177e4a3ba34dc5fe5f55))
- close ActionMenuPanel on blur so it dismisses when clicking outside ([`e1fd7aa`](https://github.com/reekeer/Rigi/commit/e1fd7aa6036e3799c7217cc06e1d6bddd43205fe))
- close ActionMenu on navigation, position NotificationRack via offset instead of dock ([`01f9e29`](https://github.com/reekeer/Rigi/commit/01f9e292bf6b5b2b6255db8c34fc931e583f65ed))
- clear existing root log handlers on install to prevent logs leaking into interface ([`7298b9f`](https://github.com/reekeer/Rigi/commit/7298b9f5ca815d4c6e15eb3992adc0aca3cc6886))
- use screen_x/screen_y for outside-click detection in overlays to prevent spurious self-removal ([`3f52ff8`](https://github.com/reekeer/Rigi/commit/3f52ff8cb788008fd0b9cf8bf9daf92dc5578a0a))
- use rgba() CSS2 format in _apply_transparency for Textual CSS parser compatibility ([`493892e`](https://github.com/reekeer/Rigi/commit/493892e3d572e092f2c00ec8c6bf7dc04bd02855))
- give Switch a fixed height:3 and width:8 so it renders correctly and is not oversized ([`dd5311c`](https://github.com/reekeer/Rigi/commit/dd5311c472d4b5bd1f41e89fb03e632e159e4a64))
- suppress textual/asyncio/PIL DEBUG logs to reduce noise in log store ([`53b7410`](https://github.com/reekeer/Rigi/commit/53b7410b7f492fb290e4802124c2ccde1de4f982))

### Changed

- bump 1.3.2 ([`ee10143`](https://github.com/reekeer/Rigi/commit/ee101438bcb1c3736a2b5647ad4fa3df521e6cf3))

### Changed

- **PR workflow:** add changelog file for summary ([`f0538b0`](https://github.com/reekeer/Rigi/commit/f0538b0367b6ef2c39d306e111f95fe64a9df17f))
- **PR workflow:** remove forks from pr summary changelog ([`ed85131`](https://github.com/reekeer/Rigi/commit/ed851319c6bec9cbd13de00aa8d4f4330b5adc83))


