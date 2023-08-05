import pandas as pd
def tables(file):
    df = pd.read_csv(file, encoding='utf-8', sep=',')
    PAP = df.iloc[:, :2]
    BOM = df.iloc[:, 2:]
    Bot = PAP[PAP["Layer"] == 'Bot']["Designator"]
    Bot = pd.DataFrame(Bot)
    Top = PAP[PAP["Layer"] == 'Top']["Designator"]
    Top = pd.DataFrame(Top)
    top_lines = 0
    bot_lines = 0
    for index, row in Bot.iterrows():
        value = str(row['Designator'])
        for index2, row2, in BOM.iterrows():
            value2 = str(row2['Designators (BOM)']).split(",")
            if value in value2:
                Bot.at[index, 'Name'] = row2["Name"]
                bot_lines += 1
    for index, row in Top.iterrows():
        value = str(row['Designator'])
        for index2, row2, in BOM.iterrows():
            value2 = str(row2['Designators (BOM)']).split(",")
            if value in value2:
                Top.at[index, 'Name'] = row2["Name"]
                top_lines += 1
    if top_lines:
        top_lines_unic = Top["Name"].nunique()
    else:
        top_lines_unic = 0
    if bot_lines:
        bot_lines_unic = Bot["Name"].nunique()
    else:
        bot_lines_unic = 0
    lines = [top_lines, top_lines_unic, bot_lines, bot_lines_unic]
    return lines