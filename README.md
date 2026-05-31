# Car Locator

Car Locator is a small mobile-friendly web app for remembering where a shared car is parked.

It supports two simple parking flows:

- `Parking Lot`: save a selected level plus optional zone and note details.
- `Street`: save the car location with GPS.

The app stores the shared parking state in Firebase Cloud Firestore so everyone using the car sees the same latest location. It also keeps a small local cache in the browser for fallback and migration purposes, and provides Google Maps links for opening or navigating to the saved location.

## Features

- Save one of four parking levels.
- Save a street parking location with GPS.
- Add optional details such as zone, section, or a note.
- See the latest shared parking spot across devices.
- Keep the current location plus the last three previous locations.
- Open the saved spot in Google Maps.
- Start navigation to the saved spot.
- Install the app on iPhone Home Screen.
- Sync updates in near real time between phones using Firebase Firestore.

## Project Files

- [index.html](/Users/mill/Documents/New project/index.html): the full app UI, styles, JavaScript, and Firebase sync logic.
- [site.webmanifest](/Users/mill/Documents/New project/site.webmanifest): PWA metadata for Home Screen install.
- [generate-icons.sh](/Users/mill/Documents/New project/generate-icons.sh): creates iPhone/PWA icon sizes from a source PNG.
- [prepare_icon.py](/Users/mill/Documents/New project/prepare_icon.py): trims and centers source artwork before icon resizing.
- [thumbnail.svg](/Users/mill/Documents/New project/thumbnail.svg): vector source for the app artwork.
- [thumbnail.png](/Users/mill/Documents/New project/thumbnail.png): rendered PNG thumbnail.

## Run Locally

Because the app is a static site, the simplest option is to open [index.html](/Users/mill/Documents/New project/index.html) in a browser.

Note: GPS features are more reliable when the app is served over `https`, especially on iPhone. Shared sync also requires internet access to reach Firestore.

## Firebase Setup

This version uses Firebase Cloud Firestore as the shared parking store.

The app expects:

- A Firebase project
- A Firestore database
- A registered Firebase web app
- Firestore enabled on the free `Spark` plan

For the first working version, Firestore can be created in `test mode`. After testing, you should tighten the Firestore security rules.

## Deploy With GitHub Pages

This project is connected to:

`https://github.com/AndersenResearchAdvisory/Parking`

To publish changes:

```bash
cd "/Users/mill/Documents/New project"
git add .
git commit -m "Describe your change"
git push
```

Then make sure GitHub Pages is enabled for the `main` branch and root folder.

Typical live URL:

`https://andersenresearchadvisory.github.io/Parking/`

## Install On iPhone

1. Open the live GitHub Pages URL in Safari.
2. Tap `Share`.
3. Tap `Add to Home Screen`.
4. Open the installed app from the Home Screen.

If the icon does not update correctly, remove the existing Home Screen icon first, refresh the page in Safari, and add it again.

To test shared sync:

1. Open the app on phone A and save a parking location.
2. Open the app on phone B with the same deployed URL.
3. Confirm the same current location appears on phone B.
4. Update the location on phone B.
5. Confirm phone A reflects the new location.

## Update App Icons

If you create a new square PNG icon source, place it in the project folder and run:

```bash
cd "/Users/mill/Documents/New project"
./generate-icons.sh Parkering.png
```

This generates:

- `apple-touch-icon.png`
- `icon-192.png`
- `icon-512.png`

The app currently references the `v5` icon files for iPhone and PWA install metadata.

## Notes

- Shared parking state lives in Firestore.
- A local browser cache is still used as a fallback and for one-time migration if Firestore starts empty.
- GPS availability depends on browser permissions and device settings.
