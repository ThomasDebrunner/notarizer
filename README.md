# Notarize

Notarize is a small python script that uses the Apple notarize API to notarize and staple your dmg.

This can be used in a CI pipeline.
Notarize invokes the standard apple tools in the background.

## What does it do?
* Upload your dmg to apple notarizations server
* Check every 30s if notarization is done
* Staple the receipt to the dmg as soon as notarization is done
* Fail (non-zero) if any of the steps above fail

## Usage

`python3 notarize.py --package <> --username <> --password <> --primary-bundle-id <>`

### Arguments

Argument | Description
---------|--------------
`--package` | The `.dmg` file to notarize
`--username` | The apple account username to be used
`--password` | The app-specific password for the user account. Can use `@env:` or `@keychain:`
`--primary-bundle-id` | The primary bundle id of your application, as specified in `Info.plist`


