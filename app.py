import json
from datetime import datetime
from time import strftime
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, ContentType
from aiogram.utils import executor
import requests
import requests.auth
from requests.auth import HTTPBasicAuth
import random
from mcstatus import MinecraftServer
import sched, time
from functools import partial
import schedule
import inspect
from copy import deepcopy
import asyncio


####CLASSES

class Job(schedule.Job):

	async def run(self):
		if (inspect.iscoroutine(self.job_func.func)
			or inspect.iscoroutinefunction(self.job_func.func)):
			ret = await self.job_func()
		else:
			ret = self.job_func()


class Scheduler(schedule.Scheduler):

	async def run_pending(self):
		global reminders_running
		runnable_jobs = (job for job in self.jobs if job.should_run)
		for job in sorted(runnable_jobs):
			ret = await job.run()
			self.cancel_job(job)
			reminders_running -= 1

	def every(self, interval=1):
		job = Job(interval, self)
		return job
		

####INITIALIZATION

#BOT INIT
bot = Bot('458818236:AAHKD2ZqGnrUF_oR2tnw_B_3UAarPbGN9Pg');
dp = Dispatcher(bot);

#VAR INIT
current_articles = []
reminders = []
oldIndex = 0;
dadjoke_counter = 0
boot_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


switch_url = "http://www.nintendo.nl"
max_results = "3"
chat_with_rudy_id = 304202876
server = MinecraftServer("127.0.0.1", 25565)
rdt_client_id = "ZFHT61P2EDsQqw"
rdt_client_secret = "MDd1gdqoZC-jPd8v3QaVqcSDBPM"
auth_stt = HTTPBasicAuth('84579377-d00d-482b-b30a-cec73327d24d', 'UbbDLhndNJM5')
auth_translate = HTTPBasicAuth('afd54602-52bd-47a9-bf95-b0001f542b63', 'mnoeLv4WmelM')

#READ SAVED FILES
smash_gifs_file  = open("smash_gifs.txt", "r")
smash_gifs = smash_gifs_file.readlines()
smash_gifs_file.close()

suggestions_file  = open("suggestions.txt", "r")
suggestions = suggestions_file.readlines()
suggestions_file.close()

#REMINDER INIT
reminders_running = 0;
current_reminders = []
sch	= Scheduler()


#HELP TEXT
help_text = """The following commands are available*:

- /help shows this message.
- /minecraft|/floop lets you know if the server is up and who is online.
- /suggest lets you suggest new features or bugfixes. The suggestions will be sent to God, who will hopefully pick it up whenever. --Format: "/suggest *suggestion*"
- /amiibo shows you a picture of the amiibo. --Format: "/amiibo *full character name*"
- /anime looks through MAL for anime listings. --Format: "/anime *search terms*"
- /xkcd will display the xkcd webcomic corresponding to the number (ID) given. --Format: "/xkcd *xkcd number*"
- /remind allows you to schedule reminders. --Format: "/remind *time* *reminder message*" where time is in minutes.
- /wiki allows you to search through wikipedia. --Format: "/wiki *search terms*"
- /dadjoke tells you a dadjoke! (BETA)
- /news show you the top news article right now. --Format: "/news" OR "/news *search terms*" for more specific news. (BETA)
- /switch looks through dutch eshop listings. Will also show if the game is currently on sale. --Format: "/switch *search terms*". (BETA)
- /steam looks through dutch steam listings. Will also show if the game is currently on sale. --Format: "/steam *search terms*". (NEW)
- /translate translates from 1 language to another. --Format: "/translate *lang* *text to translate*" where lang is the language you want to translate TO. The source language will be auto-detected.
*Some features will be done automatically and don't require a command (e.g. try saying 'smash!' anywhere in a sentence.)"""

		
####HANDLERS
	
@dp.message_handler(commands=['lastboot'])
async def lastboot_msg(message: types.Message):
	await message.reply('The bot was last booted on:' + str(boot_datetime))
	
@dp.message_handler(commands=['minecraft', 'floop'])
async def mc_server(message: types.Message):
	log(message)
	try:
		print('Trying to connect to FLOOP...')
		status = server.status()
		print('Got status')
		print(status.players.online)
		await message.reply("Floop is online and has " + str(status.players.online) + " players currently playing.")
	except e:
		print("Something went wrong, Floop may be offline.")
		await message.reply("Something went wrong, Floop may be offline.")	
		
@dp.message_handler(commands=['help'])
async def help_msg(message: types.Message):
	log(message)
	await bot.send_message(message['chat']['id'], help_text)
	
@dp.message_handler(commands=['amiibo'])
async def find_amiibo(message: types.Message):
	log(message)
	response = requests.get("http://www.amiiboapi.com/api/amiibo/?character=" + message.get_args())
	amiibos = response.json().get('amiibo');
	#print(amiibos)
	if(amiibos is None):
		await message.reply('No amiibo found with this name');
	elif(len(amiibos) == 1):
		await message.reply_photo(amiibos[0].get('image'), disable_notification=True, reply=True);
	elif(len(amiibos) > 1 and len(amiibos) <= 10):	
		imgList = []
		
		for a in amiibos:
			imgList.append(types.InputMediaPhoto(a.get('image'), "View"))
		await message.reply_media_group(imgList, disable_notification=True, reply=True);
	elif(len(amiibos) > 10):	
		imgList = []
			
		for i in range(0, 9):
			imgList.append(types.InputMediaPhoto(amiibos[i].get('image'), "View"))
		await message.reply_media_group(imgList, disable_notification=True, reply=True);	
		
@dp.message_handler(commands=['anime'])
async def find_anime(message: types.Message):
	log(message)
	try:
		response = requests.get("https://api.jikan.moe/search/anime/" + message.get_args() + "/1")
		#print(response.json().get('result')[0])
		animes = response.json().get('result');
		#if(len(animes) > 0):
		#	await message.reply(animes[0].get('url'));	
		if(len(animes) > 1):
			titles = create_data_list(animes, 'title')
			mal_ids = create_data_list(animes, 'mal_id')
			kb = create_inline_keyboard(titles, mal_ids)
			await bot.send_message(message['chat']['id'], "/anime " + message.get_args() + "\nWhich of these anime do you mean?", reply_markup = kb)
		elif(len(animes) > 0):
			await message.reply(animes[0].get('url'));			
		else:		
			await message.reply('No anime found with this name');
	except:
		await message.reply('No anime found with this name');		
		
@dp.message_handler(commands=['xkcd'])
async def find_xkcd(message: types.Message):
	log(message)
	response = requests.get("https://xkcd.com/" + message.get_args() + "/info.0.json" )
	#print(response.json())
	xkcd = response.json().get('img');
	if(xkcd is None):
		await message.reply('No xkcd found with this ID');
	elif(len(xkcd) > 0):
		await message.reply_photo(xkcd);	
		
@dp.message_handler(regexp='(smash!)')
async def smash_hype(message: types.Message):
	log(message)
	global oldIndex
	while True:
		index = random.randint(0, len(smash_gifs) - 1)
		if (index != oldIndex):
			oldIndex = index;
			break;
	await message.reply_document(smash_gifs[index], None, True, None, False);
		
@dp.message_handler(commands=['smashgif'])
async def smash_hype(message: types.Message):
	log(message)
	global smash_gifs
	try:
		await message.reply_document(message.get_args(), None, True, None, False);
		write_to("\n" + message.get_args(), "smash_gifs.txt")
	except:
		await message.reply('Not a compatible gif');
			
@dp.message_handler(commands=['suggest'])
async def suggest(message: types.Message):
	log(message)
	global suggestions
	write_to(message['from']['username'] + ": " + message.get_args() + '\n', "suggestions.txt")
	suggestions.append(message['from']['username'] + ": " + message.get_args() + '\n');
	await bot.send_message(chat_with_rudy_id, 'New suggestion\n\n' + message['from']['username'] + ': ' + message.get_args())
	await bot.send_message(message['chat']['id'], message['from']['username'] + ', your suggestion, "' +  message.get_args() + '", has been saved.');
				
@dp.message_handler(commands=['suggestions'])
async def suggestions_list(message: types.Message):
	log(message)
	global suggestions
	await message.reply('Suggestions: \n' + ''.join(suggestions));
	
@dp.message_handler(regexp='^(cool)$')
async def cool_msg(message: types.Message):
	log(message)
	await bot.send_message(message['chat']['id'], 'coolcoolcool.')
	
@dp.message_handler(regexp='\B([0-9]+!)\B')
async def factorial_msg(message: types.Message):
	log(message)
	args = message.get_args()
	print(args)
	print(message.get_command())
	await bot.send_message(message['chat']['id'], args)
	
@dp.message_handler(regexp='^(/o/)$')
async def dance_msg(message: types.Message):
	log(message)
	await bot.send_message(message['chat']['id'], '\o\\')
	await bot.send_message(message['chat']['id'], '/o/')
	await bot.send_message(message['chat']['id'], '\o\\')
	await bot.send_message(message['chat']['id'], '\o/')
	
@dp.message_handler(regexp='(good bot!)')
async def good_bot_msg(message: types.Message):
	log(message)
	await bot.send_message(message['chat']['id'], message['from']['username'] + ": 'good bot! --- *.* thank you good sir/madam! Let me know if there's anything you wish I could do by using /suggest \n\n good human!")
	
@dp.message_handler(regexp='(bad bot!)')
async def bad_bot_msg(message: types.Message):
	log(message)
	await bot.send_message(message['chat']['id'], message['from']['username'] + ": 'bad bot!'\n\n" + """....................../´¯/) 
....................,/¯../ 
.................../..../ 
............./´¯/'...'/´¯¯`·¸ 
........../'/.../..../......./¨¯\ 
........('(...´...´.... ¯~/'...') 
.........\.................'...../ 
..........''...\.......... _.·´ 
............\..............( 
..............\.............\...""")
	
@dp.message_handler(commands=['remind', 'reminder'])
async def schedule_reminder(message: types.Message):
	log(message)
	global sch
	global reminders_running
	current_reminders.append(message)
	args = message.get_args()
	arg_parts = args.split(' ')
	timer = arg_parts[0]
	arg_parts.pop(0)
	arg_text = ' '.join(arg_parts)
	try:
		sch.every(int(timer)).minutes.do(send_reminder, message, arg_text)
	except:
		await message.reply("Something went wrong. (Did you use the correct syntax?)")
		return
	if timer == "1":
		minute_text = " minute."
	else:
		minute_text = " minutes."
	await bot.send_message(message['chat']['id'], "Sir/Madam " + message['from']['username'] + ", a reminder concerning \"" + arg_text + "\" has been created. I will remind you in T minus " + timer + minute_text)
	reminders_running += 1
	if reminders_running == 1:
		asyncio.ensure_future(run_scheduler(sch))  # fire and forget
	#await sch.run_pending()
	#s = sched.scheduler(time.time, time.sleep)
	#s.enter(int(timer), 1, send_reminder, kwargs={'chat_id' : message['chat']['id'], 'message' : ' '.join(arg_parts), 'bot_clone' : bot})
	#s.run()
	
@dp.message_handler(commands=['reminders'])
async def get_reminders(message: types.Message):
	reminderText = "These are the currently running reminders:"
	for reminder in current_reminders:
		reminderText += "\n[" + datetime.now().isoformat(' ', 'seconds') + "]" + reminder['from']['username'] + ": " + reminder.text
	await message.reply(reminderText)
	
@dp.message_handler(commands=['dadjoke'])
async def dadjokes(message: types.Message):
	log(message)
	global rdt_client_id, rdt_client_secret, dadjoke_counter
	client_auth = requests.auth.HTTPBasicAuth(rdt_client_id, rdt_client_secret)
	post_data = {"grant_type": "password", "username": "shadowcraze", "password": "fantasY4!"}
	headers = {"User-Agent": "TelegramBOT/0.1 by shadowcraze"}
	response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
	#print(response.json()["access_token"])
	headers = {"Authorization": "bearer " + response.json()["access_token"], "User-Agent": "TelegramBOT/0.1 by shadowcraze"}
	response = requests.get("https://oauth.reddit.com/r/dadjokes/top/.json?sort=top&t=week", headers=headers)
	top_result = response.json()['data']['children'][dadjoke_counter]['data']
	dadjoke_counter += 1
	if dadjoke_counter > 24:
		dadjoke_counter = 0
	await bot.send_message(message['chat']['id'], top_result['title'] + "\n" + top_result['selftext'])

@dp.message_handler(commands=['wiki'])
async def wiki(message: types.Message):
	log(message)
	response = requests.get("https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch=" + message.get_args())
	pages = create_data_list(response.json()['query']['search'], 'title')
	kb = create_inline_keyboard(pages, pages)
	await bot.send_message(message['chat']['id'], "/wiki " + message.get_args() + "\nWhich of these wikipedia pages do you mean?", reply_markup = kb)

@dp.message_handler(commands=['news'])
async def news(message: types.Message):
	global current_articles
	log(message)
	args = message.get_args();
	try:
		if(len(args) > 0):
			response = requests.get('https://newsapi.org/v2/top-headlines?q=' + args + '&sortBy=popularity&apiKey=8e05f65df65840fc8bab3617d03fe5a9')
			articles = create_data_list(response.json()['articles'], 'title')
			urls = create_data_list(response.json()['articles'], 'url')
			if(len(urls) == 0):
				response = requests.get('https://newsapi.org/v2/everything?q=\"' + args + '\"&sortBy=popularity&apiKey=8e05f65df65840fc8bab3617d03fe5a9')
				articles = create_data_list(response.json()['articles'], 'title')
				urls = create_data_list(response.json()['articles'], 'url')				
			if(len(urls) == 0):
				await message.reply("No articles could be found for these search terms")
				return
			keys = [0, 1, 2, 3, 4]			
			kb = create_inline_keyboard(articles, keys)
			current_articles = urls
			await bot.send_message(message['chat']['id'], "/news " + args + "\nChoose a news article", reply_markup = kb)
			
		else:
			response = requests.get('https://newsapi.org/v2/top-headlines?country=us&apiKey=8e05f65df65840fc8bab3617d03fe5a9')
			await bot.send_message(message['chat']['id'], response.json()['articles'][0]['url'])
	except:
		await message.reply("No news articles found with these search terms: " + message.get_args())
	
@dp.message_handler(commands=['switch'])
async def switch_games(message: types.Message):
	global max_results
	log(message)
	args = message.get_args().split(' ')
	args_string = ""
	for arg in args:
		args_string += " AND title:" + arg
	response = requests.get("http://search.nintendo-europe.com/en/select/?fq=type:GAME AND system_type:nintendoswitch* AND product_code_txt:*" + args_string + "&q=*&rows=" + max_results + "&start=0&wt=json:")
	games = response.json()['response']['docs']
	#print(games)
	amount_of_results = len(games)
	if(amount_of_results > 1):
		titles = create_data_list(games, 'title')#create_titles_list(games)
		fs_ids = create_data_list(games, 'fs_id')#create_fs_id_list(games)
		kb = create_inline_keyboard(titles, fs_ids)
		#qr = types.inline_query_result.InlineQueryResultArticle(id = 'switchquery', url = "https://www.nintendo.nl/Zoeken/Zoeken-299117.html?q=*" + args + "*&f=147394-5-81", title = "Which one?", input_message_content = types.input_message_content.InputMessageContent(), reply_markup = kb)
		await bot.send_message(message['chat']['id'], "/switch " + " ".join(args) + "\nWhich of these games do you mean?", reply_markup = kb)
	elif(amount_of_results == 1):
		price_response = requests.get("https://api.ec.nintendo.com/v1/price?lang=en&country=NL&limit=5&ids=" + games[0]['nsuid_txt'][0])
		price_results = price_response.json()['prices'][0]
		price_text = price_results['regular_price']['amount']
		if('discount_price' in price_results):
			price_text += " --- currently on sale for: " + price_results['discount_price']['amount']			
		url = switch_url + games[0]['url']
		await bot.send_message(message['chat']['id'], games[0]['title'] + " - " + price_text + "\n" + url)
	else:
		await message.reply('No games found.')
	
@dp.message_handler(commands=['steam'])
async def steam_games(message: types.Message):
	log(message)
	args = message.get_args()
	response = requests.get("http://store.steampowered.com/api/storesearch/?term=" + args)
	games = response.json()['items']
	titles = create_data_list(games, 'name')#create_titles_list(games)
	ids = create_data_list(games, 'id')#create_fs_id_list(games)		
	kb = create_inline_keyboard(titles, ids)
	await bot.send_message(message['chat']['id'], "/steam " + args + "\nWhich of these games do you mean?", reply_markup = kb)	
	
#https://stream.watsonplatform.net/speech-to-text/api
#https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1?language=en-us&format=detailed
@dp.message_handler(content_types=ContentType.VOICE)
async def voice_to_text(message: types.Message):
	global watson_auth
	write_to("[" + datetime.now().isoformat(' ', 'seconds') + "]" + "Voice message sent by: " + message['from']['username'] + "\n", "SoSS_Bot log.txt")
	try:
		voice_rec = await bot.download_file_by_id(message['voice']['file_id'])
		voice_rec = bytearray(list(voice_rec.getvalue()))
		h = { 'Content-Type': 'audio/ogg'}
		response = requests.post("https://stream.watsonplatform.net/speech-to-text/api/v1/recognize", auth=auth_stt, headers = h, data = voice_rec)
		result = response.json()['results'][0]['alternatives'][0]
		await message.reply(message['from']['username'] + "(STT: " + str(round(100 * result['confidence'])) + "%): " + "\"" + result['transcript'] + "\"")
	except:
		await message.reply("Something went wrong, please try again.\nTry to speak clearly, reduce environment noise and have speech start at the start of the rcording.");
		
@dp.message_handler(commands=['translate'])
async def translate(message: types.Message):
	log(message)
	args = message.get_args().split(" ")
	if(len(args) < 2):
		await message.reply("Incorrect syntax, please check that you are using the correct syntax.")
		return
	lang = args[0]
	args.pop(0)
	origText = " ".join(args)
	text = origText.encode('UTF-8')
	try:
		h = { 'Content-Type': 'text/plain'}
		response = requests.post("https://gateway.watsonplatform.net/language-translator/api/v3/identify?version=2018-05-01", auth=auth_translate, headers = h, data=text)
		source_lang = response.json()['languages'][0]['language']
	except Exception as e:
		print(e)
		await message.reply('Couldn\'t recognize language, please try again.')
		return
	try:
		h2 = { 'Content-Type': 'application/json'}
		d = '{ "text": "' + origText + '", "source": "' + source_lang + '", "target": "' + lang + '" }'
		print(d)
		result = requests.post("https://gateway.watsonplatform.net/language-translator/api/v3/translate?version=2018-05-01", auth=auth_translate, headers = h2, data = d.encode('utf-8'))
		if("error" in result.json()):
			print(result.json()['error'])
			await message.reply('Translation from/to this language combination is not yet supported.')			
			write_to("[" + datetime.now().isoformat(' ', 'seconds') + "]" + "Translate error: " + result.json()['error'] + "\n", "SoSS_Bot log.txt")
			return			
		end_result = result.json()['translations'][0]['translation']
		await message.reply("TRANSLATION: " + end_result)
	except Exception as e:
		print(e)
		await message.reply('Translation error: not sure what went wrong...')
		return	

@dp.message_handler(commands=['currency'])
async def currency(message: types.Message):
	log(message)
	args = message.get_args().split(" ")
	if(len(args) < 3):
		await message.reply("Incorrect syntax, please check that you are using the correct syntax.")
		return
	baseCur = args[0].upper()
	targetCur = args[1].upper()
	amount = args[2]
	try:
		response = requests.get("http://data.fixer.io/api/latest?access_key=23d386d4ab1491d137c806eca41b0f55&base=" + baseCur + "&symbols=" + targetCur)
		rate = response.json()['rates'][targetCur]
		await message.reply(baseCur + str(amount) + " x " + str(rate) + " = " + targetCur + str(round(int(amount) * rate, 2)))
	except:
		await message.reply('Couldn\'t recognize currency, please try again.')

	
####CALLBACK HANDLING

@dp.callback_query_handler(func=lambda callback_query: True)
async def callback_handler(callback_query: types.CallbackQuery):
	command = callback_query.message.get_command()
	if(command == "/switch"):
		await handle_switch_callback(callback_query)
	elif(command == "/anime"):
		await handle_anime_callback(callback_query)
	elif(command == "/news"):
		await handle_news_callback(callback_query)
	elif(command == "/wiki"):
		await handle_wiki_callback(callback_query)
	elif(command == "/steam"):
		await handle_steam_callback(callback_query)
	
	
####CALLBACK HANDLERS

async def handle_switch_callback(callback_query: types.CallbackQuery):
	response = requests.get("http://search.nintendo-europe.com/en/select/?fq=type:GAME AND system_type:nintendoswitch* AND product_code_txt:* AND fs_id:" + callback_query.data + "&q=*&rows=1&sort=sorting_title asc&start=0&wt=json:")
	results = response.json()['response']['docs']
	price_response = requests.get("https://api.ec.nintendo.com/v1/price?lang=en&country=NL&limit=5&ids=" + results[0]['nsuid_txt'][0])
	price_results = price_response.json()['prices'][0]
	price_text = price_results['regular_price']['amount']
	if('discount_price' in price_results):
		price_text += " --- currently on sale for: " + price_results['discount_price']['amount']		
	if(len(results) > 0):
		callback_url = switch_url + results[0]['url'];
	else:
		callback_url = "Something went wrong"
	await bot.send_message(callback_query.message['chat']['id'], results[0]['title'] + " - " + price_text + "\n" + callback_url)
	await bot.delete_message(callback_query.message['chat']['id'], callback_query.message['message_id'])
	await callback_query.answer()
	
async def handle_anime_callback(callback_query: types.CallbackQuery):
	callback_url = "https://myanimelist.net/anime/" + str(callback_query.data)
	await bot.send_message(callback_query.message['chat']['id'], callback_url)
	await bot.delete_message(callback_query.message['chat']['id'], callback_query.message['message_id'])
	await callback_query.answer()
	
async def handle_news_callback(callback_query: types.CallbackQuery):
	global current_articles
	print(callback_query.data)
	callback_url = current_articles[int(callback_query.data)]
	current_articles = []
	await bot.send_message(callback_query.message['chat']['id'], callback_url)
	await bot.delete_message(callback_query.message['chat']['id'], callback_query.message['message_id'])
	await callback_query.answer()
	
async def handle_wiki_callback(callback_query: types.CallbackQuery):
	callback_url = "https://en.wikipedia.org/wiki/" + "_".join(callback_query.data.split(' '))
	await bot.send_message(callback_query.message['chat']['id'], callback_url)
	await bot.delete_message(callback_query.message['chat']['id'], callback_query.message['message_id'])
	await callback_query.answer()
	
async def handle_steam_callback(callback_query: types.CallbackQuery):
	callback_url = "https://store.steampowered.com/app/" + callback_query.data
	response = requests.get("http://store.steampowered.com/api/appdetails/?cc=NL&l=en-us&appids=" + callback_query.data)
	data = response.json()[callback_query.data]['data']
	title = data['name']
	if('price_overview' in data):		
		price_overview = data['price_overview']
		price_text = '€' + str(price_overview['initial'] / 100)
		if(price_overview['discount_percent'] > 0):
			price_text += " --- currently on sale for: €" + str(price_overview['final'] / 100)
	else:
		price_text = 'Free'
	await bot.send_message(callback_query.message['chat']['id'], title + " - " + price_text + "\n" + callback_url)
	await bot.delete_message(callback_query.message['chat']['id'], callback_query.message['message_id'])
	await callback_query.answer()

####HELPER FUNCTIONS	

async def send_reminder(message, text):
	await bot.send_message(message['chat']['id'], "REMINDER: " + text)#message.reply("REMINDER: " + text)
	
async def run_scheduler(scheduler):
	global reminders_running
	while reminders_running > 0:
		await scheduler.run_pending()
		await asyncio.sleep(15)
		
def reset_dadjoke_counter():
	global dadjoke_counter
	dadjoke_counter = 0;

async def run_dadjoke_scheduler(scheduler):
	while True:
		await scheduler.run_pending()
		await asyncio.sleep(3)

def log(message: types.Message):
	log_text = "[" + datetime.now().isoformat(' ', 'seconds') + "]" + message['from']['username'] + ": " + message.text
	print(log_text)
	write_to(log_text + "\n", "SoSS_Bot log.txt")
	
def write_to(text, filename):
	try:
		text_file  = open(filename, "a")
		text_file.write(text)
		text_file.close()
	except:
		return
	
def create_inline_keyboard(texts, cb_data):
	#kb = types.reply_keyboard.ReplyKeyboardMarkup(row_width = 1,one_time_keyboard = True)
	kb = types.inline_keyboard.InlineKeyboardMarkup(1)
	for i in range(len(texts)):
		#button = types.reply_keyboard.KeyboardButton(text = "/s1 " + texts[i])
		button = types.inline_keyboard.InlineKeyboardButton(text = texts[i], callback_data = cb_data[i])
		kb.insert(button)
	return kb

def create_data_list(data, field, max_count = 5):
	data_list = []
	counter = 0
	for d in data:
		data_list.append(d[field])
		counter += 1
		if(counter == max_count):
			break
	return data_list
		
def create_titles_list(games):
	titles = []
	titles.append(games[0]['title'])
	titles.append(games[1]['title'])
	if(len(games) > 2):
		titles.append(games[2]['title'])
	return titles

def create_fs_id_list(games):
	fs_ids = []
	fs_ids.append(games[0]['fs_id'])
	fs_ids.append(games[1]['fs_id'])
	if(len(games) > 2):
		fs_ids.append(games[2]['fs_id'])
	return fs_ids
		
	

#code to run
#dad_sch	= Scheduler()
#dad_sch.every().minute.do(reset_dadjoke_counter)
#asyncio.ensure_future(run_dadjoke_scheduler(dad_sch))

if __name__ == '__main__':
	executor.start_polling(dp)
	