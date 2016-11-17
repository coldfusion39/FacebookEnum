#!/usr/bin/env python
import argparse
import re
from FacebookEnum import FacebookEnum


def main():
	parser = argparse.ArgumentParser(description='Facebook account enumeration using the forgotten password feature.')
	parser.add_argument('target', help='Email, username, full name, or phone number', nargs='+')
	args = parser.parse_args()

	fbook = FacebookEnum()
	results = fbook.enum(' '.join(args.target))
	if results:
		for result in results:
			print_results(' '.join(args.target), result)
	else:
		print_error("No Facebook account found for {0}".format(' '.join(args.target)))


# Print account information
def print_results(target, result):
	print_good("Account information for {0}".format(target))
	print("Name: {0}".format(result['name']))
	print("Location: {0}".format(result['location']))

	if result['phone']:
		for phone in result['phone']:
			print("Phone: {0}".format(phone))

	if result['email']:
		for email in result['email']:
			print("Email: {0}".format(email))

	print("Picture: {0}\n".format(result['picture']))


def print_error(msg):
	print("\033[1m\033[31m[-]\033[0m {0}".format(msg))


def print_good(msg):
	print("\033[1m\033[32m[+]\033[0m {0}".format(msg))


if __name__ == '__main__':
	main()
