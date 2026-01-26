# yaque
Yet another Queens game

TODO:
 - apk build process on github, save a github secret to use as a hash for daily games, package into apk.
 - game repeatability via random seed
 - sqlite database of played games
 - calendar, one month display with 3 stars in each for 6,7, and 8 daily games, show streak. 
 - new game popup: select field size and game uniqueness
 - during splashscreen generate daily games for sizes 6,7 and 8
 - main screen: 3 daily challenges, calendar, logbook, random game, settings? exit
 - Before time starts show only gray game field. 'Play' button to show the game and start the clock
 - 'pause' button hides the field and stops the clock
 - for random game add 'share' button and do a QR code with cusom url scheme: `yaque://start?level=42&field=6`
