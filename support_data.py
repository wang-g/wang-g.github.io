from __future__ import division
from bs4 import BeautifulSoup
import urllib2
import re

def url_request(url):
    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36',
           'Accept':'*/*'}
    request = urllib2.Request(url, headers=hdr)
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        print e.fp.read()
        quit()
    return response

def support_skill_row(skill_name, skill_tag_and_costs):
    row = skill_name + "|"
    attr_tag = skill_tag_and_costs[0]
    mana_mults = skill_tag_and_costs[1]
    row += attr_tag + "|"
    if type(mana_mults) is list:
        for t in mana_mults:
            row += str(t[0]) + "-" + str(t[1]) + ","
        row = row[:-1]
    else:
        row += str(mana_mults)
    return row+"\n"

def get_support_info(html):
    bs = BeautifulSoup(html)

    # First, tries finding mana cost information in the gem progression table
    gem_prog_table = bs.find('table', {'class': 'wikitable GemLevelTable'})
    if gem_prog_table == None:              #returns if gem progression table not found
        return None
    first_row = gem_prog_table.find('tr')   #finds first row, the header row
    prog_headers = first_row.find_all('th')       #gets a list of the column labels
    mana_mult_col = -1
    for i in range(len(prog_headers)):
        header_text = prog_headers[i].text
        if "Mult." in header_text:
            mana_mult_col = i
            break
    if mana_mult_col != -1:                 #if no column labeled "Mana Cost" was found, return None
        mana_mults = []
        for row in first_row.find_next_siblings('tr'):
##            print row
            row_entries = row.find_all(['th','td'])
            level_entry = row.find('th').text.strip()
            mana_entry = row_entries[mana_mult_col].text.strip().strip('%')
            try:
                mana_mults.append((int(level_entry),int(mana_entry)/100))
            except ValueError:
                continue
        return mana_mults
    else:
        return None

def find_supports(bs, search_phrase, attr_tag, support_dict):
    header = bs.find('th', text = re.compile(search_phrase))
    support_headers = header.find_next_siblings('th')
    mcm_col = -1
    for i in range(len(support_headers)):
        if support_headers[i].text == 'MCM':
##            print "header_location: " + str(i + 1)
            mcm_col = i + 1
            break
    table = header.find_parent('table')
    rows = table.find_all('tr')
    base_url = 'http://pathofexile.gamepedia.com/'
    support_list = []
    for r in rows:
        link = r.find('a')
        if link == None:
            continue
        skill_name = link.text.strip()
        print skill_name
        row_entries = r.find_all('td')
        mcm_entry = row_entries[mcm_col]
        mcm = None
        if 'N/A' in mcm_entry.text:
            mcm = 1
        elif '*' in mcm_entry.text:
            url = base_url + link['href']
            response = url_request(url)
            support_html = response.read()
            mcm = get_support_info(support_html)
        else:
            try:
                mcm = int(mcm_entry.text.strip().strip('%'))/100
            except ValueError:
                mcm = None
        if not mcm == None:
            support_dict[skill_name] = (attr_tag, mcm)
        else:
            print "OH NO: " + skill_name
        

url = 'http://pathofexile.gamepedia.com/Skills'
base_url = 'http://pathofexile.gamepedia.com'

response = url_request(url)

sk_html = response.read()

bs = BeautifulSoup(sk_html)

support_dict = {}

find_supports(bs, 'Strength Support Gems', 'str', support_dict)
find_supports(bs, 'Dexterity Support Gems', 'dex', support_dict)
find_supports(bs, 'Intelligence Support Gems', 'int', support_dict)

support_file = open('support_file.txt', 'w')
for support in support_dict:
    if type(support_dict[support][1]) is list and len(support_dict[support][1]) < 20:
        support_file.write("--")
    support_file.write(support_skill_row(support, support_dict[support]))
support_file.close()
