# wfm-helper
Helper scripts for [warframe.market](https://warframe.market).

*DISCLAIMER: I don't know JavaScript. I'm just following common sense.*

### `wfm-ext` (Chrome Extension)  
A Chrome extension that displays the ducat value of a prime component next to its name on warframe.market. 
* How it works:
    - When you visit a user profile on warframe.market, the extension automatically displays the ducat value next to each prime component.
    - Values are color-coded:
        + **Red** for items with a ducat value below 45.
        + **Green** for items with a ducat value of 45 or above.
        + **Gold** for items that meet either of these conditions:
            * Price is 1 platinum and 45 or more ducats.
            * Price is 2 platinum or less and 90 or more ducats.

    ![warframe.market profile preview](img/warframe-market.png)

### `wfm-ntfy` (Python Script)  
A Python script that monitors new sell orders on warframe.market and sends notifications based on specific price and ducat value conditions.
* How it works:
    - Connects to the warframe.market websocket and listens continuously.
    - Alerts when an item meets one of the following conditions:
        + Price is 1 platinum and 45 or more ducats.
        + Price is 2 platinum or less and 90 or more ducats.
    - When these conditions are met, the script:
        + Prints a message to the console.
        + Sends a notification through a pub-sub service.

    ![phone notifications preview](img/phone.png)
    ![terminal preview](img/terminal.png)
