filename = "./data/zzztest.log"
filename2 = "./data/zzztest2.log"
keepline =41648
# open file and remove the first 500 lines
with open(filename, 'r') as file:
    lines = file.readlines()

# remove the first 500 lines
if len(lines) > keepline:
    lines = lines[:keepline]

# write the remaining lines to a new file
with open(filename2, 'w') as file:
    file.writelines(lines)
