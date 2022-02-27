# -*- coding: utf-8 -*-

import discord
from async_google_trans_new.constant import LANGUAGES

locations = {'europe': 57000000, 'north america': 57000001, 'south america': 57000002, 'asia': 57000003,
             'oceania': 57000004, 'africa': 57000005, 'international': 57000006, 'afghanistan': 57000007,
             'åland islands': 57000008, 'albania': 57000009, 'algeria': 57000010, 'american samoa': 57000011,
             'andorra': 57000012, 'angola': 57000013, 'anguilla': 57000014, 'antarctica': 57000015,
             'antigua and barbuda': 57000016, 'argentina': 57000017, 'armenia': 57000018, 'aruba': 57000019,
             'ascension island': 57000020, 'australia': 57000021, 'austria': 57000022, 'azerbaijan': 57000023,
             'bahamas': 57000024, 'bahrain': 57000025, 'bangladesh': 57000026, 'barbados': 57000027,
             'belarus': 57000028, 'belgium': 57000029, 'belize': 57000030, 'benin': 57000031, 'bermuda': 57000032,
             'bhutan': 57000033, 'bolivia': 57000034, 'bosnia and herzegovina': 57000035, 'botswana': 57000036,
             'bouvet island': 57000037, 'brazil': 57000038, 'british indian ocean territory': 57000039,
             'british virgin islands': 57000040, 'brunei': 57000041, 'bulgaria': 57000042, 'burkina faso': 57000043,
             'burundi': 57000044, 'cambodia': 57000045, 'cameroon': 57000046, 'canada': 57000047,
             'canary islands': 57000048, 'cape verde': 57000049, 'caribbean netherlands': 57000050,
             'cayman islands': 57000051, 'central african republic': 57000052, 'ceuta and melilla': 57000053,
             'chad': 57000054, 'chile': 57000055, 'china': 57000056, 'christmas island': 57000057,
             'cocos (keeling) islands': 57000058, 'colombia': 57000059, 'comoros': 57000060, 'congo (drc)': 57000061,
             'congo (republic)': 57000062, 'cook islands': 57000063, 'costa rica': 57000064, 'côte d’ivoire': 57000065,
             'croatia': 57000066, 'cuba': 57000067, 'curaçao': 57000068, 'cyprus': 57000069, 'czech republic': 57000070,
             'denmark': 57000071, 'diego garcia': 57000072, 'djibouti': 57000073, 'dominica': 57000074,
             'dominican republic': 57000075, 'ecuador': 57000076, 'egypt': 57000077, 'el salvador': 57000078,
             'equatorial guinea': 57000079, 'eritrea': 57000080, 'estonia': 57000081, 'ethiopia': 57000082,
             'falkland islands': 57000083, 'faroe islands': 57000084, 'fiji': 57000085, 'finland': 57000086,
             'france': 57000087, 'french guiana': 57000088, 'french polynesia': 57000089,
             'french southern territories': 57000090, 'gabon': 57000091, 'gambia': 57000092, 'georgia': 57000093,
             'germany': 57000094, 'ghana': 57000095, 'gibraltar': 57000096, 'greece': 57000097, 'greenland': 57000098,
             'grenada': 57000099, 'guadeloupe': 57000100, 'guam': 57000101, 'guatemala': 57000102, 'guernsey': 57000103,
             'guinea': 57000104, 'guinea-bissau': 57000105, 'guyana': 57000106, 'haiti': 57000107,
             'heard & mcdonald islands': 57000108, 'honduras': 57000109, 'hong kong': 57000110, 'hungary': 57000111,
             'iceland': 57000112, 'india': 57000113, 'indonesia': 57000114, 'iran': 57000115, 'iraq': 57000116,
             'ireland': 57000117, 'isle of man': 57000118, 'israel': 57000119, 'italy': 57000120, 'jamaica': 57000121,
             'japan': 57000122, 'jersey': 57000123, 'jordan': 57000124, 'kazakhstan': 57000125, 'kenya': 57000126,
             'kiribati': 57000127, 'kosovo': 57000128, 'kuwait': 57000129, 'kyrgyzstan': 57000130, 'laos': 57000131,
             'latvia': 57000132, 'lebanon': 57000133, 'lesotho': 57000134, 'liberia': 57000135, 'libya': 57000136,
             'liechtenstein': 57000137, 'lithuania': 57000138, 'luxembourg': 57000139, 'macau': 57000140,
             'macedonia (fyrom)': 57000141, 'madagascar': 57000142, 'malawi': 57000143, 'malaysia': 57000144,
             'maldives': 57000145, 'mali': 57000146, 'malta': 57000147, 'marshall islands': 57000148,
             'martinique': 57000149, 'mauritania': 57000150, 'mauritius': 57000151, 'mayotte': 57000152,
             'mexico': 57000153, 'micronesia': 57000154, 'moldova': 57000155, 'monaco': 57000156, 'mongolia': 57000157,
             'montenegro': 57000158, 'montserrat': 57000159, 'morocco': 57000160, 'mozambique': 57000161,
             'myanmar (burma)': 57000162, 'namibia': 57000163, 'nauru': 57000164, 'nepal': 57000165,
             'netherlands': 57000166, 'new caledonia': 57000167, 'new zealand': 57000168, 'nicaragua': 57000169,
             'niger': 57000170, 'nigeria': 57000171, 'niue': 57000172, 'norfolk island': 57000173,
             'north korea': 57000174, 'northern mariana islands': 57000175, 'norway': 57000176, 'oman': 57000177,
             'pakistan': 57000178, 'palau': 57000179, 'palestine': 57000180, 'panama': 57000181,
             'papua new guinea': 57000182, 'paraguay': 57000183, 'peru': 57000184, 'philippines': 57000185,
             'pitcairn islands': 57000186, 'poland': 57000187, 'portugal': 57000188, 'puerto rico': 57000189,
             'qatar': 57000190, 'réunion': 57000191, 'romania': 57000192, 'russia': 57000193, 'rwanda': 57000194,
             'saint barthélemy': 57000195, 'saint helena': 57000196, 'saint kitts and nevis': 57000197,
             'saint lucia': 57000198, 'saint martin': 57000199, 'saint pierre and miquelon': 57000200,
             'samoa': 57000201, 'san marino': 57000202, 'são tomé and príncipe': 57000203, 'saudi arabia': 57000204,
             'senegal': 57000205, 'serbia': 57000206, 'seychelles': 57000207, 'sierra leone': 57000208,
             'singapore': 57000209, 'sint maarten': 57000210, 'slovakia': 57000211, 'slovenia': 57000212,
             'solomon islands': 57000213, 'somalia': 57000214, 'south africa': 57000215, 'south korea': 57000216,
             'south sudan': 57000217, 'spain': 57000218, 'sri lanka': 57000219, 'st. vincent & grenadines': 57000220,
             'sudan': 57000221, 'suriname': 57000222, 'svalbard and jan mayen': 57000223, 'swaziland': 57000224,
             'sweden': 57000225, 'switzerland': 57000226, 'syria': 57000227, 'taiwan': 57000228, 'tajikistan': 57000229,
             'tanzania': 57000230, 'thailand': 57000231, 'timor-leste': 57000232, 'togo': 57000233, 'tokelau': 57000234,
             'tonga': 57000235, 'trinidad and tobago': 57000236, 'tristan da cunha': 57000237, 'tunisia': 57000238,
             'turkey': 57000239, 'turkmenistan': 57000240, 'turks and caicos islands': 57000241, 'tuvalu': 57000242,
             'u.s. outlying islands': 57000243, 'u.s. virgin islands': 57000244, 'uganda': 57000245,
             'ukraine': 57000246, 'united arab emirates': 57000247, 'united kingdom': 57000248,
             'united states': 57000249, 'uruguay': 57000250, 'uzbekistan': 57000251, 'vanuatu': 57000252,
             'vatican city': 57000253, 'venezuela': 57000254, 'vietnam': 57000255, 'wallis and futuna': 57000256,
             'western sahara': 57000257, 'yemen': 57000258, 'zambia': 57000259, 'zimbabwe': 57000260}
cr_locations = ', '.join(k for k in locations.keys())
cr_locations_embed = discord.Embed(title='Clash Royale location list',
                                   description=cr_locations)

joke_category_embed = discord.Embed(title='Select a Category')
nsfw_embed = discord.Embed(
    title='By having NSFW jokes turned on, you agree that all users are mature enough to handle them')
religious_embed = discord.Embed(
    title='By having Religious jokes turned on, you agree that users may take offense from some jokes')
political_embed = discord.Embed(
    title='By having Political jokes turned on, you agree that users may have conflicting political views and may take offense')
sexist_embed = discord.Embed(
    title='By having Sexist jokes turned on, you agree that users may take offense from some jokes')
racist_embed = discord.Embed(
    title='By having Racist jokes turned on, you agree that users may take offense from some jokes')
explicit_embed = discord.Embed(
    title='By having Explicit turned on, you agree that all users are mature enough to handle them')
alert_bed = discord.Embed(
    title='We are not responsible for any jokes that make any users or goups, feel discomfort or feel offended.')
confirm_bed = discord.Embed(title='New settings confirmed!',
                            description='You may not involve us with any user sensitive jokes')
cancel_bed = discord.Embed(title='New settings cancelled.')


lang_bed = discord.Embed(title='List of Languages',
                         description='\n'.join(f'{k}/{v}' for k, v in LANGUAGES.items()))