#!/usr/bin/env python
import re
import requests
from bs4 import BeautifulSoup


class FacebookEnum(object):
	def __init__(self):
		self.session = requests.Session()
		self.HEADERS = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate, br',
			'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
			'Referer': 'https://www.facebook.com/login/identify?ctx=recover&lwv=110',
			'Connection': 'close'
		}

	def enum(self, target):
		account_info = None

		recovery_urls = self._get_tokens(target)
		if recovery_urls:
			account_info = self._get_recovery_info(target, recovery_urls)

		return account_info

	# Get cookies and tokens
	def _get_tokens(self, target):
		recovery_urls = []

		request = self.session.get('https://www.facebook.com/recover/initiate?lwv=110', headers=self.HEADERS)
		if request.status_code == 200:
			js_regex = re.search('"_js_datr","(.+)",[0-9]{11},', request.text)
			lsd_regex = re.search('{"token":"([a-zA-Z0-9_-]{8})"}', request.text)
			rev_regex = re.search('{"revision":([0-9]{7}),"tier"', request.text)
			if js_regex and lsd_regex and rev_regex:
				js_token = js_regex.group(1)
				lsd_token = lsd_regex.group(1)
				rev_token = rev_regex.group(1)

				cookies = {'_js_datr': js_token}

				data = {
					'lsd': lsd_token,
					'email': target,
					'did_submit': 'Search',
					'__user': '0',
					'__a': '1',
					'__req': '3',
					'__rev': rev_token
				}

				# Send LDATA request
				request = self.session.post('https://www.facebook.com/ajax/login/help/identify.php?ctx=recover&__pc=EXP1:DEFAULT', headers=self.HEADERS, cookies=cookies, data=data)
				if request.status_code == 200:
					ldata_multi_regex = re.findall('([a-z0-9_-]{174})&(?:amp;)?ldata=([a-z0-9_-]{259})', request.text, re.I)
					ldata_regex = re.search('ldata=([a-z0-9_-]{259})', request.text, re.I)

					# Multiple accounts found
					if ldata_multi_regex:
						for ldata in ldata_multi_regex:
							recovery_url = "https://www.facebook.com/login/identify?ctx=recover&cuid_selected={0}&ldata={1}".format(ldata[0], ldata[1])
							recovery_urls.append(recovery_url)

					# Single account found
					elif ldata_regex:
							recovery_url = "https://www.facebook.com/recover/initiate?ldata={0}&_fb_noscript=1".format(ldata_regex.group(1))
							recovery_urls.append(recovery_url)

					# No accounts found
					else:
						pass

		return recovery_urls

	# Parse account information
	def _get_recovery_info(self, target, urls):
		found_accounts = []

		target_type = self._identify_target(target)

		for url in urls:
			account = {
				'name': None,
				'location': None,
				'email': None,
				'phone': None,
				'picture': None
			}

			request = self.session.get(url, headers=self.HEADERS)
			if request.status_code == 200:
				soup = BeautifulSoup(request.text, 'lxml')

				try:
					if ' ' in target and (soup.find('div', attrs={'class': 'fsl fwb fcb'}).text).encode('UTF-8') != target:
						pass
					else:
						account['name'] = (soup.find('div', attrs={'class': 'fsl fwb fcb'}).text).encode('UTF-8')

					# Get location
					account['location'] = (soup.find('div', attrs={'class': 'fsm fwn fcg'}).text).encode('UTF-8')

					# Get account recovery options
					connected_contact = soup.findAll('div', attrs={'class': '_8u _42ef'})
					for contact in connected_contact:
						single_contant = contact.findAll('div')
						for div in single_contant:

							# Get recovery phone numbers
							phones = []
							phone_regex = re.search('^(\+\*.+)', div.text, re.I)
							if phone_regex:
								phones.append((phone_regex.group(1)).encode('UTF-8'))

							# Get recovery emails
							emails = []
							email_regex = re.search('^([*a-z0-9._-]{1,}@[a-z0-9-]{1,}\.[a-z]{2,})', div.text, re.I)
							if email_regex:
								emails.append((email_regex.group(1)).encode('UTF-8'))

					account['phone'] = phones
					account['email'] = emails

					# Get small profile picture
					picture_regex = re.search('/profile/pic.php\?cuid=([a-z0-9_-].*&amp;square_px=50)', request.text, re.I)
					if picture_regex:
						account['picture'] = "https://www.facebook.com/profile/pic.php?cuid={0}".format(picture_regex.group(1))

					found_accounts.append(account)

				except AttributeError:
					pass

		return found_accounts

	# Identify target type
	def _identify_target(self, target):
		if '@' in target:
			target_type = 'email'
		elif re.match('[0-9]{10,11}', target):
			target_type = 'phone'
		elif ' ' in target:
			target_type = 'name'
		else:
			target_type = 'username'

		return target_type
