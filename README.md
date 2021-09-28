# MoleBot

MoleBot (despite its name) is a Discord bot program that can do slightly complicated things for a Minecraft server ([Civclassic](https://github.com/CivClassic)) I play on. For example:
- Calculates pretty complicated /dest commands to travel the server while AFK
- Can find dest locations or settlements on the map when given coordinates
- Relays wiki pages when requested
- Pings the server when requested

## How to use:
- Download the repository
- Check `requirements.txt` and `pip install` as necessary
- Set the following fields in the environment variables:
  - Your discord bot ID (app_id=xxxxxxxxxx)
  - Your discord bot token (token=xxxxxxxxxx)
  - Your PostgreSQL database URL (preferably a Heroku PostgreSQL server) (DATABASE_URL=xxxxxxxx)
- Run the server

If you did this correctly, the bot will launch. It's as easy as that!

## Commands/Features
Command | Description
---|---
/civwiki or [[link]]| Gets a wikipage from https://civwiki.org/, a wiki for the Civ genre of Minecraft servers
/config|Changes the behavior of certain commands, currently has options for `/civwiki` and `/mole` commands/features
/dest|Calculates the destination commands required from destination to destination (using KANI or AURA system dest locations)
/disablemole|Currently does the same thing as `/config mole`.
"delusional"|Displays a link to Edit CivWiki (this is a joke command)
/finddests|Finds the closest destination areas to enter **(KANI only)**
/help|Displays a help command, or can display help on a single command
/invite|Invites this bot to another server
/mole|Shows a mole (this is a joke command)
/ping|Pings the default server (CivClassic, currently hardcoded) or another server
/whereis|Finds the closest settlements from a location
/whois|Looks up a player's information (alt-history & name changes from Mojang)

## Questions/Concerns

For any bugs, please create an issue and I will fix it as soon as possible!

For any questions, contact specificlanguage#2893.

