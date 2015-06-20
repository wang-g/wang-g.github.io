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

def get_skill_info(html):
    bs = BeautifulSoup(html)

    # First, tries finding mana cost information in the gem progression table
    gem_prog_table = bs.find('table', {'class': 'wikitable GemLevelTable'})
    if gem_prog_table == None:              #returns if gem progression table not found
        return None
    first_row = gem_prog_table.find('tr')   #finds first row, the header row
    prog_headers = first_row.find_all('th')       #gets a list of the column labels
    mana_cost_col = -1
    for i in range(len(prog_headers)):
        header_text = prog_headers[i].text
        if "Mana" in header_text and "Cost" in header_text:
            mana_cost_col = i
            break
    if mana_cost_col != -1:                 #if no column labeled "Mana Cost" was found, return None
        mana_costs = []
        for row in first_row.find_next_siblings('tr'):
##            print row
            row_entries = row.find_all(['th','td'])
            level_entry = row.find('th').text.strip()
            mana_entry = row_entries[mana_cost_col].text.strip()
            try:
                mana_costs.append((int(level_entry),int(mana_entry)))
            except ValueError:
                continue
        return mana_costs

    # If no mana cost information is found in the gem progression table,
    # then checks the gem infobox
    gem_infobox = bs.find('table', {'class': 'GemInfoboxContainer'})
    infobox_mana_reserved = gem_infobox.find('td', text=re.compile('Mana Reserved'))
    infobox_mana_label = gem_infobox.find('td', text=re.compile('Mana Cost'))
    if not infobox_mana_reserved == None:   #if this skill reserves mana, it has no mana cost
        return None
    elif not infobox_mana_label == None:
        infobox_mana = infobox_mana_label.find_next_sibling().text.strip()
        try:
            return int(infobox_mana)
        except ValueError:
            return None
    else:
        return None

def active_skill_row(skill_name, skill_tag_and_costs):
    row = skill_name + "|"
    attr_tag = skill_tag_and_costs[0]
    mana_costs = skill_tag_and_costs[1]
    row += attr_tag + "|"
    if type(mana_costs) is list:
        for t in mana_costs:
            row += str(t[0]) + "-" + str(t[1]) + ","
        row = row[:-1]
    else:
        row += str(mana_costs)
    return row+"\n"

def find_skills(bs, search_phrase, attr_tag):
    headers = bs.find_all('th', text=re.compile(search_phrase))
    header = ''
    for h in headers:
        if len(h.find_next_siblings('th')) < 4:
            header = h
            break
    table = header.find_parent('table')
    rows = table.find_all('tr')
    base_url = 'http://pathofexile.gamepedia.com/'
    skill_list = []
    for r in rows:
        link = r.find('a')
        if link == None:
            continue
        skill_name = link.text.strip()
        url = base_url + link['href']
        skill_list.append((skill_name, attr_tag, url))
    return skill_list

url = 'http://pathofexile.gamepedia.com/Skills'
base_url = 'http://pathofexile.gamepedia.com'

response = url_request(url)

sk_html = response.read()

bs = BeautifulSoup(sk_html)

##str_headers = bs.find_all('th', text=re.compile('Strength Skills'))
##str_header = ''
##for h in str_headers:
##    if len(h.find_next_siblings('th')) == 3:
##        str_header = h
##        break
##str_table = str_header.find_parent('table')
##str_rows = str_table.find_all('tr')
##base_url = 'http://pathofexile.gamepedia.com/'

skill_list = []
skill_list.extend(find_skills(bs, 'Strength Skills', 'str'))
skill_list.extend(find_skills(bs, 'Dexterity Skills', 'dex'))
skill_list.extend(find_skills(bs, 'Intelligence Skills', 'int'))
skill_list.extend(find_skills(bs, 'Other Skills', 'oth'))

skills_dict = {}
no_cost_list = []

for s in skill_list:
    print s[0]
    response = url_request(s[2])
    skill_html = response.read()
    mana_costs = get_skill_info(skill_html)
    print str(mana_costs)
    if mana_costs == None:
        no_cost_list.append(s[0])
    else:
        skills_dict[s[0]] = (s[1], mana_costs)

##for r in str_rows:
##    link = r.find('a')
##    if link == None:
##        continue
##    skill_name = link.text.strip()
##    print skill_name
##    url = base_url + link['href']
##    response = url_request(url)
##    skill_html = response.read()
##    mana_costs = get_skill_info(skill_html)
##    print str(mana_costs)
##    if mana_costs == None:
##        no_cost_list.append(skill_name)
##    else:
##        skills_dict[skill_name] = mana_costs

mana_file = open('mana_file.txt', 'w')
for skill in skills_dict:
    if type(skills_dict[skill][1]) is list and len(skills_dict[skill][1]) < 20:
        mana_file.write("--")
    mana_file.write(active_skill_row(skill, skills_dict[skill]))
mana_file.write("===NO_COST===\n")
for skill_name in no_cost_list:
    mana_file.write(skill_name + "\n")
mana_file.close()
