from HPK_data_checks.error_checker import Data

dirpaths = ["../_All_HPK-prepro-data"]
Datlas18 = Data(dirpaths)

flags = Datlas18.flags
print("PRINTING WAFER FLAGS:")
for k in sorted(list(flags.keys())):
    print(k,flags[k])
#format of flags: {"<SN>":"OK|WARNING|ERROR", ...}
