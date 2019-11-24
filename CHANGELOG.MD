Changelog
=========


v1.1.0 (2019-11-19)
-------------------
- Improved changelog generation. [BR]
- Total stats GUI is able to fetch last N matches. [BR]
- Added changelog, makefile changelog script. [BR]
- Added api for fetching badges/total stats from last N matches. [BR]


v1.0.1 (2019-11-18)
-------------------
- Improved minor images, small css fixes. [BR]


v1.0.0 (2019-11-17)
-------------------
- Fixed tests. [BR]
- Added basic presence list. Fix #48. [BR]
- Create pythonpublish.yml. [BR]
- Added pypi badges to readme. [BR]


v0.13.0 (2019-11-17)
--------------------
- Improved installation guide (pip included) [BR]
- Added proper bumpversion config. [BR]
- Don't add 0 score for specting clients. [BR]
- Fixed KDR calculation for non playing clients. [BR]
- Fixed bug when 0 badges can be assigned, improved KDR calculation.
  [BR]


v0.12.0 (2019-10-01)
--------------------
- Fixed mismatched version. [BR]
- Improved top badgers panel. [BR]
- Added suicide bomber badge, Fix #46. [BR]
- Slightly improved badges descriptions. [BR]
- Added consecutive rail kill badge, Fix #34. [BR]
- Improved number of badges visible on homepage. [BR]
- Added badge images for suicide bomber and consecutive rail. [BR]


v0.11.0 (2019-08-25)
--------------------
- Added Marauder badge, Fix #43. [BR]


v0.10.0 (2019-06-09)
--------------------
- Further cleanup in readme file. [BR]
- Improved readme file. [BR]
- Improved test data discovery, use native py3 mock. [BR]
- Added initial CLI, moved around some code. [BR]
- Updated readme, added dev requirements. [BR]


v0.9.61 (2019-05-12)
--------------------
- Added printable option for player view. [BR]
- Added basic frontend support for health/armor/damage stats. [BR]
- Added more logging and exception handling. [BR]
- Added full backend support for match player stats. [BR]
- Added initial support for Weapon_Stats log entry. [BR]
- Moved some test code. [BR]
- Added lumberjack medal. [BR]
- Added lumberjack medal (consecutive gauntlet kills) [BR]
- Added new badge - Ghost Kill. [BR]
- Added match end indicator on score chart Fix #38. [BR]
- Added color generation by player id - Fix #37. [BR]
- Selected player is easier to see now. [BR]
- Its possible to select all player occurance on match page. [BR]
- Added kamikaze badge Fix #35. [BR]
- Code cleanup, Use events instead of dicts. [BR]
- Unified the way test data is generated. [BR]
- Refactored player switch team event. [BR]
- Refactored player kill/death events and their usage. [BR]
- Added analysis event class - not to use raw dicts. [BR]
- Moved PlayerScores tests to separate file. [BR]
- Moved PlayerScores to separate file. [BR]
- Moved TeamLifecycle class to separate file. [BR]
- Count world when assigning multi medals. [BR]
- Another cleanup in tests. [BR]
- Moved ql match feeder to separate file. [BR]
- Moved q3toql to separate file. [BR]
- Moved q3 MatchFeeder to separate file. [BR]
- Moved FullMatchInfo to separate file. [BR]
- Updated classdoc, moved MatchFeeder to separate file. [BR]
- Extracted MatchPreprocessor from dataprovider init. [BR]
- Fixed typo in Readme. [BR]
- Added headhunter marks on score chart Fix #32. [BR]
- Improve README.md about install pip packages and remove Twisted from
  requirements. [Klaudiusz Mrosek]
- Add missing markdown in README. [Klaudiusz Mrosek]
- Add new line in README.md after last changes. [Klaudiusz Mrosek]
- Add Twisted to requirements. [Klaudiusz Mrosek]
- Added info to use recent twisted lib. [BR]
- Added player kills/deaths details, Fix #31. [BR]
- Added testcase and comment for winner badges assignment. Fix #30. [BR]
- Fixed dev links in Readme. [BR]
- Slightly reorganized tests. [BR]
- Reorganized code for Badger. [BR]
- Reorganized code for SpecialScores. [BR]
- Assign less medals if not enough players Fix #24. [BR]
- Added app version info to base template. [BR]
- Updated setup.py according to pypa, better make clean. [BR]
- Score summary is now properly ordered Fix #29. [BR]
- Added simple api to import preprocessed matches. [BR]
- Update README.md. [BR]
- Added missing newline. [BR]
- Added build information. [BR]
- Added setup.py develop to travis.yml. [BR]
- Cleaned up requirements.txt. [BR]
- Added .travis.yml. [BR]
- Version  bump. [BR]
- Added headless knight badge fix #28. [BR]
- Use newer Flask-pymongo Fix #26. [BR]
- PlayerScores are now initialized on MatchStarted, Fix #27. [BR]
- HEADHUNTER is now properly calculated in corner cases. Fix #25. [BR]
- Added mosquito badge, Fix #15. [BR]
- Added badges to player info. [BR]
- Use 4 columns instead of 6 for player weapon stats. [BR]
- Added total games to player view, added more top targets/enemies. [BR]
- Added top 5 enemies/targets fix #21. [BR]
- Added telefrag icon. [BR]
- Added basic player summary fix #17. [BR]
- Added requirements. [krzysztofsmokowski]
- Don't calculate fav weapon if player killed nothing. Fix #19. [BR]
- Fav weapon is now correctly calculated, Fix #13. [BR]
- Changed weapon stats title. [BR]
- Slightly changed layout and added weapon deaths. [BR]
- Better gauntlet icon. [BR]
- Added systemd example. Fix #11. [BR]
- Frontend will load kill info first. [BR]
- More backend requests in parallel. [BR]
- Added BFG icon, weapon order in weapon kills. [BR]
- Added weapon kill stats. Fix #12. [BR]
- Version bump. [BR]
- Added vengeance medal to frontend. [BR]
- Added vengeance medal in backend. [BR]
- Fixed linting errors. [BR]
- Added score details for DREADNOUGHT medal. [BR]
- Bugfix, ingore lifespan medal if state is empty. [BR]
- Added medal for long life (Fix #6) [BR]
- Special score details are now rendered as table. [BR]
- Added popup to special score details (Fix #8) [BR]
- Added proper popup window for badge info. [BR]
- Players on badge board are sorted by total amount of badges. [BR]
- HEADHUNTER/DUCKHUNTER no longer takes q3-world under consideration.
  [BR]
- Player merge will now survive DB rebuild. [BR]
- Disconnected players are no longer counted in player-score list. [BR]
- Fixed linting errors. [BR]
- Added map rating. [BR]
- Added weapon slime. [BR]
- Added assets for emo, star, crapcake, weapon gauntlet. [BR]
- Added title to badge images, improved badge description. [BR]
- Added some more badge assets. [BR]
- Added assets for win_almost badge. [BR]
- Reordered badge resources, minor improvement in readme file. [BR]
- Added footer with github link, fixes #1. [BR]
- Added youlose badge and lava fav weapon icons. [BR]
- Added badge swine. [BR]
- Added more weapon icons. [BR]
- Added railgun icon. [BR]
- Fixes #4, ability to remove specific match and related info. [BR]
- Added sample q3 match file. [BR]
- Removed vim temp files. [BR]
- Added codebase. [BR]
- Initial commit. [BR]


