#Author  : Dhruv Ramani (dhurvramani98@gmail.com)
#License : Apache-2.0

import os
import sys
import time
import zipfile
from selenium import webdriver
from getpass import getpass

try:
	from configparser import SafeConfigParser
except ImportError:
	from ConfigParser import SafeConfigParser


chrome_options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options.add_experimental_option("prefs",prefs)
driver = webdriver.Chrome(chrome_options = chrome_options)
driver.set_window_size(1080,800)  #Required, removes the "element not found" bug

replyButton = None
customCommands = {}

try:
	input = raw_input
except NameError:
	pass

def clear():
	if os.name == 'nt':
		os.system('cls')
	else : 
		os.system('clear')

def zipdir(path, ziph):
	for root, dirs, files in os.walk(path):
		for file in files:
			ziph.write(os.path.join(root, file))

def waitForNextMessage():
	driver.implicitly_wait(10)
	messageList = driver.find_elements_by_css_selector('.null')
	command = ''
	while True:
		driver.implicitly_wait(10)
		element = driver.find_elements_by_css_selector('.null')
		if element != messageList:
			command = element[-1].find_elements_by_css_selector("*")[0].text
			if not(command.split('\n')[0] == '@CLI'):
				print(command)
				runCommand(command)
			break
		time.sleep(0.1)

def runCommand(command):
	driver.implicitly_wait(10)
	output = os.popen(command).read()
	url = fpath = ''
	cmd = command.lower().split(' ')
	if (len(cmd) >= 2):
		fpath = os.getcwd()+'/'+' '.join(cmd[1:])
		urlIden = cmd[1].split(':')[0]
		if  urlIden == 'http' or urlIden == 'https':
			url = cmd[1]
	
	if (len(cmd) >= 4):
		if cmd[0] == 'set' and cmd[2] == 'as':
			global customCommands
			if cmd[1] not in customCommands:
				final = ' '.join(cmd[3:])
				with open('commands.txt','a') as foo:
					foo.write(cmd[1] + ' ' + final + '\n')
				customCommands[cmd[1]] = final
				output = 'Command set : {} = {}'.format(cmd[1], final)
			else: 
				output = 'ERROR\nCommand already defined : {}'.format(cmd[1])

	if cmd[0] in customCommands:
		output = os.popen(customCommands[cmd[0]]).read() 

	if cmd[0] == 'senddir':
		name = ''.join(cmd[1:])+'.zip'
		if os.path.isdir(fpath):
			zipf = zipfile.ZipFile(name, 'w')
			zipdir(fpath, zipf)
			zipf.close()
			driver.find_element_by_id('js_1').send_keys(os.getcwd()+'/'+name)
			output = fpath
		else:
			output = 'ERROR\nNo such directory: {}'.format(fpath)

	if cmd[0] == 'cd':
		if os.path.isdir(fpath):
			os.chdir(fpath)
			output = os.getcwd()
		else : 
			output = 'ERROR\nNo such directory: {}'.format(fpath)

	if cmd[0] == 'send':
		if os.path.isfile(fpath):
			driver.find_element_by_id('js_1').send_keys(fpath)
			output = fpath
		else:
			output = 'ERROR\nFile not found : {}'.format(fpath)
	if cmd[0] == 'quit':
		print('Session Ended')
		driver.quit()
		sys.exit(0)

	if cmd[0] == 'show':
		dr = webdriver.Chrome()
		foo = True
		if url:
			dr.get(url)
		elif os.path.isfile(fpath):
			dr.get('file:///'+fpath)
		else :
			output = 'Invalid Path/URL : ' 
			foo = False

		if foo:
			dr.save_screenshot('ss.png')
			dr.quit()
			if url:
				output = url 
			else: 
				utput = fpath
			driver.find_element_by_id('js_1').send_keys(os.getcwd() +  '/ss.png')

	if cmd[0] == 'memory':
		if os.name == 'nt':
			output = 'ERROR\nCurrently, the memory command is only supported for UNIX-based machines'
		else:
			output = os.popen('top -l 1 -s 0 | grep PhysMem').read()
	if cmd[0] == 'help':
		output = 'help : Displays this\n\nquit : Ends current session\n\nsend __filePath : Sends the file at the path specfied\n\nsenddir __dirPath : Sends directory after coverting to .zip\n\nmemory : Gives current memory stats of system\n\nshow __filePath/URL : Previews file/url \n\nset *NewCommandName* as *actualCommand* : Define alias name for command\n\n------USER DEFINED ALIAS------\n\n'+'\n'.join(customCommands.keys())+'\n\n------------\n\nRun any other command as you would on your CLI'
	
	if not output:
		output = '(Y)'
		
	driver.find_element_by_css_selector('.uiTextareaNoResize.uiTextareaAutogrow._1rv').send_keys('@CLI\n\n'+output)
	driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
	replyButton.click()

def init():
	cont = False
	clear()

	credentials_from_file = False

	credentials = SafeConfigParser();
	credentials.read('settings.txt')
	if (credentials.has_option('main','email') 
		  and credentials.has_option('main','password')):
		credentials_from_file = True

	while not cont:
		driver.get('https://www.facebook.com/')
	
		if credentials_from_file:
			email = credentials.get('main', 'email')
			password = credentials.get('main', 'password')
		else:
			email = input('Email : ')
			password = getpass('Password : ')

		inputs=driver.find_elements_by_tag_name('input')
		inputs[1].send_keys(email)
		inputs[2].send_keys(password)
		driver.implicitly_wait(10)
		inputs[3].click()

		if str(driver.current_url).split('=')[0] == 'https://www.facebook.com/login.php?login_attempt':
			clear()
			print('Invalid Email/Password')
			if credentials_from_file:
				print('Switching to manual input')
				credentials_from_file = False
		else: 
			cont = True

	print('Loading...\n')
	profile = [x for x in driver.find_elements_by_tag_name('a') if x.get_attribute('title') == 'Profile'][0].get_attribute('href').split('/')[3]
	driver.get('https://www.facebook.com/messages/'+profile)
	
	global replyButton
	replyButton = [x for x in driver.find_elements_by_tag_name('input') if x.get_attribute('value') == 'Reply'][0]

	if not(replyButton.is_displayed()):
		driver.find_element_by_css_selector('._1s0').click()

	if os.path.isfile(os.getcwd() + '/commands.txt'):
		with open('commands.txt','r') as foo:
			for a in foo.read().split('\n'):
				ls = a.split(' ')
				if len(ls) >= 2:
					global customCommands
					customCommands[ls[0]] = ' '.join(ls[1:])

	print('Ready!\n\n--------------COMMANDS--------------')


def login_fast():
	from robobrowser import RoboBrowser
	from bs4 import BeautifulSoup as bs

	browser = RoboBrowser(history=True)
	browser.open('https://m.facebook.com/')
	#FORM FILL
	form = browser.get_form()
	form['email'].value=mail
	form['pass'].value=password
	browser.submit_form(form)
	#PARSER (can also be implemented from robobrowser)
	soup = browser.parsed
	try:
		soup = soup.find("label", {"for" : "u_0_0"})
		username = soup.a
		username.clear()
		username = str(username)
		profile = username[username.find('/')+1 : username.find('?')]
		#print (profile)
	except:
		print("wrong credentials!")

if __name__ == '__main__':
	init()
	while True:
		waitForNextMessage()
		time.sleep(0.1)
