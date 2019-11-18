#whosthatchampionbot is a discord bot that utilizes discord.py and riot games api to set the nickname
#of a discord user to whatever champ they are playing.


try:
    #clears the screen
    import os
    os.system("clear")
    #i delete os here to mitigate any vulnerabilities that might be discovered.
    del os

    #time library is used to prevent over-usage of the api key
    import time

    #requests is used for api code
    import requests

    #discord is used for bot api
    import discord

    #for task scheduling
    from threading import Thread


    #champs is just a data file with a dictionary of champion ids.
    #it was cluttering up the main file, so i stuck it in a library
    import champs
    champions=champs.champions

    #auth keys
    import auth
    token=auth.token
    api_key=auth.api_key

    #data.py is a single line file with a dictionary in it. 
    #i use it to link discord IDs to summoner names
    import data
    player_data=data.player_data

    #last update timestamp refers to the last time that the data.py file was updated.
    last_update_timestamp=int(time.time())

    #initializes the discord bot client.
    client=discord.Client()



    #runs once the bot is ready to go
    @client.event
    async def on_ready():
        #lets me know that the bot is logged in
        print('logged in as {0.user}'.format(client))

    #runs whenever someone posts a message in the discord.
    @client.event
    async def on_message(message):
      
        #checks to see if the bot sent the message
        if message.author == client.user:

            #if so, return
            return

        #'>' is the command prefix. 
        if message.content.startswith('>'):

            #this chunk preps the command message for parsing
            #removes the command prefix and splits each argument into a list
            message_in_list_form=message.content.replace('>','',1).split()

            #command is the first element of the list
            command=message_in_list_form[0]

            #args is a list of command arguments
            args=message_in_list_form[1:]

            #logs commands to console
            print("command from user {}: {}".format(message.author,message.content.replace('>','',1)))


            #now for the command handling
            
            #if the command is >ping
            if command=="ping":

                #sends a reply to tell the user that the bot is, in fact, running
                await message.channel.send(
"""```css
Pong!
```"""
                    )

            #if the command is >set
            #set command has one argument, the formatted summoner name ()
            elif command=="set":
                
                #a formatted version of the summoner name in case the user didnt do it already
                formatted_summoner_name=str(''.join(args[0:])).replace(' ','').replace("'","").lower()
                #this api call is used to run a check to make sure that the user has provided a valid summoner name
                test_player_data=requests.get("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}{}".format(formatted_summoner_name,api_key))
                #status code 200 is the 'all clear' code. anything else is an error
                if test_player_data.status_code == 200:
                    
                    #try block to catch any possible errors from the data storage
                    try:
                        
                        #player_data is the dictionary defined at the beginning of the file
                        player_data[message.author.id]=[formatted_summoner_name,message.author.nick,int(time.time())]

                        #this block opens data.py, clears it, then writes the updated dictionary to it
                        await update_file()

                        #lets the user knows that command worked
                        await message.channel.send(
"""```css
Done! your discord is now linked to {}. If you wish to ever change this, just use >set again!
```""".format(args[0])
                        )

                    #if an error is thrown
                    except:
                        await message.channel.send(
"""```asciidoc
[Oops! something went wrong in the data editing. Please try again later or try >help for help]
== Thanks! ==
```"""
                    )

                #if the status code is an error
                else: 
                    await message.channel.send(
"""```asciidoc
[Oops! something went wrong in the api request. Please try again later or try >help for help]
== Thanks! ==
```"""
                    )
                    print(test_player_data.status_code)

            #help command
            elif command=="help":
                await message.channel.send(
"""```yaml
help: Displays this command
e.g. >help
```

```yaml
language: displays programming info
e.g. >language
```
```yaml
set: when combined with a summoner name, links your league of legends account to the bot
e.g. >set Da Pi Guy 3
```
```yaml
reset: sets your nickname to whatever it was the last time you used the set command
e.g. >reset
```"""
                )
            
            #sends a python emoji because why not

            elif command=='python' or command=='language':
                await message.channel.send(
"""```python
>>> this bot was written in python3 using discord.py
```"""
            )

            #manually fixes nick
            elif command=='reset':
                await message.author.edit(nick=player_data[message.author.id][1])

            #if the command isn't recognized by the code
            else:
                await message.channel.send(
"""```asciidoc
[Oops! that command isnt recognized! Please try again later or try >help for help]
== Thanks! ==
```"""
                )

    #function that waits 45 minutes before setting targetmember's nick to their preset nick
    async def timer_thread(modded_nick, targetmember):
        #sleep for  45 minutes
        time.sleep(45*60)

        #checks to see if the nick is the same as the one set by the program 45 minutes ago
        if targetmember.nick==modded_nick:

            #if so, reset the nick
            await targetmember.edit(nick=player_data[targetmember.id][1])
    
    #function that wraps timer_thread into a loop and runs it
    async def run_timer_thread(targetmember):
        #creates the thread object
        newthread=Thread(target=timer_thread(targetmember))
        #starts the thread
        newthread.start()


    #grabs the champion name using two api requests
    def Get_Champion(personinput):

        #api call for the summoner info. this is only used to grab the encrypted_summoner_id in order to retrieve live match data
        response=requests.get('https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}{}'.format(str(personinput),api_key))

        #formats the json into a dictionary
        testdict=dict(response.json())

        #try catch block makes sure that an error isnt handled if a user somehow managed to get an invalid
        #summoner name into the data file.
        try:

            #grabs the encrypted summoner id
            encrypted_summoner_id=testdict['id']

            #api call for live match data
            response_2=requests.get("https://na1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{}{}".format(encrypted_summoner_id,api_key))

            #if there is no live match data available
            if response_2.status_code==404:
                
                #theres a blank champion entry in champs.py that has NULL as an ID to catch this.
                championID="NULL"
            
            elif response_2.status_code==429:
                championID="NULL"
            
            elif response_2.status_code==403:
                print('forbidden')
            
            #if there is live match data:
            else:

                #converts the api json into a dictionary
                championID0=dict(response_2.json())

                #grabs the participants list from said dictionary
                championID1=championID0["participants"]

                #iterates through the players to find the dictionary with the matching summone id
                for n in range(0,len(championID1)):

                    #this is because i dont wanna have x[y][z][s]  in my code
                    thisdude=championID1[n]

                    #grabs the summoner name and formats it down to the same format as the one in data.py,
                    #then runs a check
                    if thisdude["summonerName"].replace(' ','').lower()==personinput:
                        
                        #if it passes, we got our man
                        championID2=championID1[n]

            #sets championID variable to the champion id
            championID=championID2["championId"]

            #cross references championID with the champions dictionary and returns the result
            return(champions[championID])

        #'handles' any other errors that might get thrown during api stuff
        except:
            pass

    #function for updating the data file
    async def update_file():
        
        #checks to see if file has been updated in the last 30 seconds
        if int(time.time())-last_update_timestamp>=30000:

            #updates the timestamp
            last_update_timestamp=int(time.time())

            #opens the file, tuncates it, writes to it, and then closes it.
            datafile=open('data.py','w')
            output_string='player_data={}'.format(player_data)
            datafile.truncate()
            datafile.write(output_string)
            datafile.close()

    #this block triggers whenever someone's voice state updates
    #that could be a join, leave, mute, unmute, deafen, or undeafen event.
    @client.event
    async def on_voice_state_update(target_member, VC1, VC2):

        #checks to see if it was a member joining a channel
        if VC1.channel == None and VC2.channel != None:

            #this reduces the amount of unneccesary api calls by putting a 5 second cooldown on everything
            #whenever a user triggers a voice_state update, <player_data[user.id][2]> is updated to a current timestamp.
            #then a simple subtraction is done to determine if the timedelta of the two is more than 10,000 (10 seconds)
            #if so, it triggers, running the commands and updating the timestamp; if not, it ignores it
            if int(time.time()) - player_data[target_member.id][2] >= 10000:

                #block handles errors that could be thrown from setting the nick
                try:

                    #grabs the player's discord id
                    player_name=player_data[target_member.id][0]

                    #sends the id to the champion function, which will return the champion name
                    champ_name=Get_Champion(player_name)

                    #sets the nickname
                    await target_member.edit(nick=champ_name)

                    player_data[target_member.id][2]=int(time.time())
                    print('timer passed')

                    run_timer_thread(target_member)
                
                #'handles' the error
                except KeyError:
                    pass
                    print('timer exceded')
            
            else:
                pass

    #now that the rest of the code is out of the way, it's time to start the bot
    client.run(token)

#handles anything that might interrupt the code
#it will back up player_data to its storage file before closing
except:
    data=open('data.py','w')
    data.truncate()
    data.write("player_data={}".format(player_data))
    data.close()

