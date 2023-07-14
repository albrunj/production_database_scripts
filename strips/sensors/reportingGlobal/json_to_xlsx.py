import json
from datetime import datetime

import xlsxwriter

colwidths = {
            'ShipmentName':40,
            'ShipmentDate':15,
            'ShipmentStatus':10,
            'ShipmentID':15,
            'From':5,
            'To':5,
            'SS':3,'LS':3,'R0':3,'R1':3,'R2':3,'R3':3,'R4':3,'R5':3,'DUMMY':3,
            'batch':12,
            'ingot':12,
            'arrivalDate':12,
            'sensor':15,
            'origLocation':5,
            'currentLocation':5,
            'Sensors not at origLocation':5,
            'Total QA minis':6,
            'Total QA chips':6,
            'Wafer Numbers':6,
}

def emptyseq(row):
    for val in row:
        if val != '':
            return False
    return True

def datestr(date):
    if date == '' or type(date) != str: date = '31/12/9999'
    return datetime.strptime(date,"%d/%m/%Y")

def lightercolor(hexcolor):
    nums = [int(hexcolor[i:i+2],base=16) for i in range(1,7,2)]
    newnums = [n + (255-n)//2 for n in nums]
    newhexcolor = '#'
    for n in newnums:
        newhexcolor += hex(n).upper()[2:]
    return newhexcolor

def write_summary_to_xlsx(outfilepath,values_json,formatting_json,summary_type='shipment',sortBy='ShipmentDate'):
    with open(values_json,'r') as values_jsonfile:
        origvalues = json.load(values_jsonfile)
    with open(formatting_json,'r') as formatting_jsonfile:
        origformattings = json.load(formatting_jsonfile)

    header_row = 7
    rstart = header_row + 1
    sortable_headers = ['sensor','ShipmentName','ShipmentDate','arrivalDate','batch','ingot','origLocation','currentLocation']
    if sortBy not in sortable_headers:
        raise Exception("SortBy '{}' not allowed (not in {})".format(sortBy,sortable_headers))
    headers = origvalues[header_row][:origvalues[header_row].index('Wafer Numbers')+1]
    if sortBy not in headers:
        raise Exception("SortBy '{}' not in headers".format(sortBy))
    sortByIndex = headers.index(sortBy)
    zipped_data = zip(origvalues[rstart:],origformattings[rstart:])

    #standard python native sorter, low to high (or alphabetical)
    if 'date' in sortBy.lower():
        if sortBy == 'arrivalDate':
            #special sorter for dd/mm/yyyy
            sorted_data = sorted(zipped_data,key=lambda vf: datestr(vf[0][sortByIndex]))
        else:
            sorted_data = sorted(zipped_data,key=lambda vf: vf[0][sortByIndex])
    else:
        sorted_data = sorted(zipped_data,key=lambda vf: vf[0][sortByIndex])
        
        #after custom sort, sort blocks by arrivalDate or ShipmentDate

        #get markers to help with sorting
        markers = [0]
        for i in range(1,len(sorted_data)):
            if sorted_data[i][0][0] != sorted_data[i-1][0][0]:
                markers.append(i)

        #re-sort blocks based on date
        if origvalues[header_row][1] == 'arrivalDate':
            #sort by arrival date the blocks between markers
            for i in range(len(markers)-1):
                block = sorted_data[markers[i]:markers[i+1]]
                sorted_data[markers[i]:markers[i+1]] = sorted(block,key=lambda vf: datestr(vf[0][1]))
        elif origvalues[header_row][1] == 'ShipmentDate':
            #just sort these dates normally
            for i in range(len(markers)-1):
                block = sorted_data[markers[i]:markers[i+1]]
                sorted_data[markers[i]:markers[i+1]] = sorted(block,key=lambda vf: vf[0][1])
        else:
            print("COULD NOT SORT GROUPS")

    #add the header rows first, then the data rows
    values = list(origvalues[:rstart])
    formattings = list(origformattings[:rstart])
    for dat in sorted_data:
        values.append(dat[0])
        formattings.append(dat[1])


    workbook = xlsxwriter.Workbook(outfilepath)
    worksheet = workbook.add_worksheet('DBSummary')
    worksheet.freeze_panes(rstart, 0)
    worksheet.insert_image('A1', 'atlasitk.png')
    headers = list(values[rstart-1])
    for c in range(len(headers)):
        if headers[c] == '':
            worksheet.set_column(c,c,colwidths['Wafer Numbers'])
            continue
        #set column to appropriate width (colwidths)
        try:
            if headers[c].startswith('NG') or (headers[c].startswith('NG-ATLAS18') and headers[c].endswith('V1')) or headers[c] == 'NG-MANUFACTURING18':
                cw = 6
            else:
                cw = colwidths[headers[c]]
            worksheet.set_column(c,c,cw)
        except Exception as e:
            raise(e)

    #preprocess sheet to trim empty columns/rows
    trimmed_values = []
    trimmed_formattings = [] 
    for row in range(len(values)):
        if emptyseq(values[row]) and row > rstart:
            continue
        trimmed_values.append([])
        trimmed_formattings.append([])
        for col in range(len(values[row])):
            if emptyseq(values[row][col:]):
                break
            value = values[row][col]
            formatting = formattings[row][col]
            trimmed_values[-1].append(value)
            trimmed_formattings[-1].append(formatting)

    #now write to xlsx
    for row in range(len(trimmed_values)):
        for col in range(len(trimmed_values[row])):
            value = trimmed_values[row][col]
            formatting = trimmed_formattings[row][col]
            #add borders for grouping similar cells
            if row < header_row:
                formatting['border'] = 0
            elif row == header_row:
                #could use different font?
                pass 
            else: #for all data rows below header
                if col == 0:
                    if value != trimmed_values[row-1][col]:
                        formatting['top'] = 5
                        for c in range(len(trimmed_values[row])):
                            trimmed_formattings[row][c]['top'] = 5


                #color currently-uncolored cells of each column a lighter color than the header of that column
                if formatting.get('bg_color') in ['white','#FFFFFF',None]:
                    formatting['bg_color'] = lightercolor(trimmed_formattings[header_row][col]['bg_color'])
                    if row % 2 == 0:
                        formatting['bg_color'] = lightercolor(formatting['bg_color'])
                        

                #make values bold in "header" columns like NG-HPK
                if col < len(trimmed_values[header_row]):
                    header = trimmed_values[header_row][col]
                    if (header.startswith('NG-ATLAS18') and header.endswith('V1')) or (header == 'NG-MANUFACTURING18'):
                        formatting['bold'] = True
                        formatting['left'] = 5

            hyperlink = None
            if formatting.get('link') != None:
                hyperlink = formatting['link']
                #formatting['font_color'] = '#0000FF'
                del formatting['link']
    
            cell_format = workbook.add_format(properties=formatting)

            if hyperlink != None:
                worksheet.write_url(row,col,hyperlink,string=value,cell_format=cell_format)
            else:
                worksheet.write(row,col,value,cell_format)
    workbook.close()

def main(args):
    write_summary_to_xlsx(args.outfile,'tmpvalues.json','tmpformatting.json',args.summaryType,args.sortBy)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'Specialized inventory summary from json buffers to local XLSX')
    parser.add_argument('-o', '--outfile', dest = 'outfile', type = str, default = 'output.xlsx', help = 'outfile name')
    parser.add_argument('-t','--summaryType', dest = 'summaryType',type=str,default = 'shipment', help = 'summary type (shipment | batch)')
    parser.add_argument('-s','--sortBy',dest = 'sortBy',type=str,default = 'ShipmentDate',help = 'which column to sort rows by (pick any column header)')
    args = parser.parse_args()

    main(args)
