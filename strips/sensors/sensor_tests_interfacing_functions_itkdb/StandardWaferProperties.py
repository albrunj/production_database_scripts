mm=1e-3
cm=1e-2

AreaDict={
    'Unknown':(97.621-0.450)*(97.950-0.550)*mm*mm,
    #
    'ATLAS12': 95.7*95.64*mm*mm,
    'ATLAS17LS': (97.621-0.450)*(97.950-0.550)*mm*mm,
    #
    'ATLAS18R0':89.9031*cm*cm,
    'ATLAS18R1':89.0575*cm*cm,
    'ATLAS18R2':74.1855*cm*cm,
    'ATLAS18R3':80.1679*cm*cm,
    'ATLAS18R4':87.4507*cm*cm,
    'ATLAS18R5':91.1268*cm*cm,
    #
    'ATLAS18SS':93.6269*cm*cm,
    'ATLAS18LS':93.6269*cm*cm,
    #
    'ATLASDUMMY18':(97.621-0.450)*(97.950-0.550)*mm*mm,
}

StripLengthDict = {}
StripLengthDict['Unknown'] = 48.36 *mm
#
StripLengthDict['ATLAS17LS'] = 48.36*mm
StripLengthDict['ATLAS17SS'] = 24.18*mm 
#
StripLengthDict['ATLAS18R0'] = {
    1: 18.37*mm,
    2: 23.21*mm,
    3: 28.20*mm,
    4: 31.21*mm
}
#
StripLengthDict['ATLAS18R1'] = {
    1: 17.33*mm,
    2: 26.32*mm,
    3: 23.32*mm,
    4: 14.48*mm
}
#
StripLengthDict['ATLAS18R2']={
    1: 30.04*mm,
    2: 30.04*mm
}
#
StripLengthDict['ATLAS18R3']={
    1: 25.46*mm,
    2: 31.45*mm,
    3: 31.45*mm,
    4: 25.46*mm,
}
#
StripLengthDict['ATLAS18R4']={
    1: 53.82*mm,
    2: 53.97*mm,
}
#
StripLengthDict['ATLAS18R5']={
    1: 39.40*mm,
    2: 59.55*mm,
}
#
StripLengthDict['ATLAS18SS'] = 24.16*mm 
StripLengthDict['ATLAS18LS'] = 48.35*mm
#
StripLengthDict['ATLASDUMMY18'] = 48.36*mm
