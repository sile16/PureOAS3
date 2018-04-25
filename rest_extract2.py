from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox,LTChar, LTFigure
import sys
import re
from string import digits
from pprint import pprint
import json
import random
from datetime import datetime


class PdfMinerWrapper(object):
    """
    Usage:
    with PdfMinerWrapper('2009t.pdf') as doc:
        for page in doc:
           #do something with the page
    """
    def __init__(self, pdf_doc, pdf_pwd="",laparams=None):
        self.pdf_doc = pdf_doc
        self.pdf_pwd = pdf_pwd
        self.laparams = laparams
 
    def __enter__(self):
        #open the pdf file
        self.fp = open(self.pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(self.fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument(parser, password=self.pdf_pwd)
        # connect the parser and document objects
        parser.set_document(doc)
        self.doc=doc
        return self
    
    def _parse_pages(self):
        rsrcmgr = PDFResourceManager()
        if self.laparams == None:
            laparams = LAParams( all_texts = True)
        else:
            laparams=self.laparams
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
    
        for page in PDFPage.create_pages(self.doc):
            
            interpreter.process_page(page)
            # receive the LTPage object for this page
            layout = device.get_result()
            
            # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
            yield layout
    def __iter__(self): 
        return iter(self._parse_pages())
    
    def __exit__(self, _type, value, traceback):
        self.fp.close()
            
def main(laparams=None):
    with PdfMinerWrapper("REST_API_1.13.pdf",laparams) as doc:
        
        resource_found = False
        machine = ["f","fd","e","ed",""]
        state = machine[0]
        line = ""
        fontname = ""
    
        x_coordinate = 0.0 #The distance from left edge of page
        middle_x=0.0


        paths = {}
        path=""
        
        example_name=""
        tags=[]
        tag=""

        param_index=0
        tag_index=0

        path_id=""
        

        count=0
        for page in doc:     
            #print 'Page no.', page.pageid, 'Size',  (page.height, page.width)
            if page.pageid == 74:
                pass

            items=[]
            for tbox in page:
                
                if not isinstance(tbox, LTTextBox):
                    continue
                #print ' '*1, 'Block', 'bbox=(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                for obj in tbox:
                    #print ' '*2, obj.get_text().encode('UTF-8')[:-1] #,  '(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                    line = obj.get_text().strip() #.encode('UTF-8')[:-1]

                    
                    for c in obj:
                        if not isinstance(c, LTChar):
                            continue 

                        fontname = c.fontname
                        #size = str(c.size) #.encode('UTF-8')
                        break
                    
                    items.append(
                        {'text':obj.get_text().strip(),
                        'box':tbox.bbox,
                        'font':fontname}
                        )

            sorted_items = pdf_sort(items)

            for row in sorted_items:
                for item in row['items']:

                    line = item['text']
                    
                    if line.startswith("Resources") and item['font'] == "Arial,Bold" :
                        resource_found = True
                    
                    
                    if resource_found:                   
                        x_coordinate = item['box'][0]
                        #print line.encode('UTF-8')
                        #print '({}|{}|{}|{})'.format( c.fontname, c.size,type(c.size),tbox.bbox[0])

                        if re.match(r"^[0-9]+\. ",line):
                            #Match section identifiers
                            # i.e.  1. Authentication
                            tag = line.split(" ")[1]
                            tags.append({"name":tag,"description":""})
                            tag_index = len(tags)-1
                            
                            
                            state="fd"
                            continue
                        
                        elif re.match(r"^[0-9]+\.[0-9]+ ",line):

                            #Match endpoint
                            # i.e. "2.1 GET array"
                            tag_index +=1
                            temp = line.split(" ")
                            method = temp[1].lower()
                            path = "/"+temp[2]
                            if path not in paths:
                                paths[path] = {}
                            paths[path][method] = {"tags":[tag],
                                                      "description":"",
                                                      "operationId":method+path,
                                                      "responses": {
                                                           '200':{
                                                               "content":{
                                                                   "application/json":{
                                                                       "schema":{}
                                                                   }
                                                               },
                                                               "description":""
                                                           }
                                                       }  
                                                    }
                                                

                            

                            param_index=0
                            if method=="get" or method == "delete" or "{" in path:
                                paths[path][method]['parameters'] = []
                            
                            #Need to create path param for each {id1} .. {id2} in path
                            
                            for path_id in re.findall(r'\{(.*?)\}',path):
                                #adding in special path parameter volume/{volumeid}  example
                                #add "Id" to the param name to avoid name conflicts according ot Oas 3 spec
                                path_id += "Id"
                                paths[path][method]['parameters'].append({"name":path_id,"in":"path","required":True,"schema":{"type":"string"}})
                                param_index += 1

                            if not method=="get" and not method=="delete" :
                                #paths[path][method]['requestBody'] = {'content':{"application/json":{"schema":{"properties":{}}}}}
                                paths[path][method]['requestBody'] = {'content':{"application/json":{"schema":{"properties":{},"type":"object"}}}}

                            state="ed"
                            continue
                        
                        elif line.startswith("Parameters"):
                            
                            state="parameters"
                            continue

                        elif line.startswith("Parameter"):
                            
                            state="parameters"
                                
                            continue

                        elif line.startswith("Example "):
                            state="example"
                            #split = line.split()
                            example_name = line
                            #folders[title]['endpoints'][endpoint]['examples'][example_name] = {"description":line,"request":"","response":""}
                            if 'examples' not in paths[path][method]["responses"]["200"]["content"]["application/json"]:
                                paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"]={}
                            paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name] = {"value":{"request":"","response":""}}
                            continue
                        
                        elif line.startswith("Request:"):
                            state="example_request"
                            continue
                        
                        elif line.startswith("Response:"):
                            state="example_response"
                            continue
                        

                        
                        

                        
                        if state == "fd":
                            tags[tag_index]['description'] += line

                        elif state == "ed":
                            paths[path][method]['description'] += line

                        elif state.startswith("parameters"):
                            if "Bold" in item['font']:
                                #This is a header, we will ignore these.
                                continue

                            if state == "parameters_3":
                                if x_coordinate < middle_x:
                                    #this means we wrapped around and are now on a new param.
                                    state = "parameters"
                                    param_index +=1

                            if state == "parameters":
                                #first param
                                param_name = line
                                if param_name != "None":
                                    #folders[title]['endpoints'][endpoint]['params'][param_name] = {"description":"",'required':None}
                                    if  method == "get" or  method == "delete":
                                        paths[path][method]['parameters'].append({"in":"query","name":param_name,"description":"","schema":{}})

                                    else :
                                        #paths[path][method]['requestBody'] = {'content':{"application/json":{"schema":{"properties":{},"type":"object","required":[]}}}}
                                        #paths[path][method]['requestBody'] = {'content':{"application/json":{"schema":{"properties":{},"type":"object","required":[]}}}}
                                        paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name] = {"description":""}
                                        

                                state = "parameters_2"
                                if " " not in line:
                                    #sometimes the type is concatenated with the param_name, we can detect if there is a space in name.
                                    continue
                                else:
                                    line = line.split(" ",1)[1]
                                    #now we will roll into param2 parsing.

                            if state == "parameters_2":
                                #type
                                if param_name != "None":
                                    #folders[title]['endpoints'][endpoint]['params'][param_name]['type'] = line
                                    if  method == "get" or  method == "delete":
                                        paths[path][method]['parameters'][param_index]['schema']['type']= getType(line)
                                    else:
                                        paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name]['type'] = getType(line)

                                state = "parameters_3"
                                middle_x = x_coordinate
                                if  len(line) < 17:
                                    #means the descirptions was so close the pdf parser grouped it with the type text:
                                    continue
                                


                            if state == "parameters_3":
                                if param_name != "None":
                                    if line == "Required.":
                                        #folders[title]['endpoints'][endpoint]['params'][param_name]['required'] = True
                                        if  method == "get" or  method == "delete":
                                            paths[path][method]['parameters'][param_index]['required']= True
                                        else:
                                            if 'required' not in paths[path][method]['requestBody']['content']['application/json']['schema']:
                                                paths[path][method]['requestBody']['content']['application/json']['schema']['required'] = []
                                            paths[path][method]['requestBody']['content']['application/json']['schema']['required'].append(param_name)
                                    #elif line == "Optional.":
                                        #folders[title]['endpoints'][endpoint]['params'][param_name]['required'] = False
                                    else:
                                        if  method == "get" or  method == "delete":
                                            paths[path][method]['parameters'][param_index]['description'] += line
                                        else:
                                            paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name]['description'] += line
                        
                        #end elif state.startswith("parameters"):

                        elif state.startswith("example_request"):
                            if state == "example_request":
                                #split = line.split()
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['method'] = split[0]
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['url'] = split[1]
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['body'] = ""
                                
                                paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]["value"]['request'] += line
                                state="example_request_2"
                                continue
                                
                                #paths[path][method]["responses"]["200"]['examples'][example_name]['request'] += line
                                
                            else:
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['body'] += line
                                #paths[path][method]["responses"]["200"]['examples'][example_name]['request'] += line
                                paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]["value"]['request'] += line
                                continue
                            
                    
                            

                        elif state == "example_response":
                            #folders[title]['endpoints'][endpoint]['examples'][example_name]['response'] += line
                            #paths[path][method]["responses"]["200"]['examples'][example_name]['response'] += line
                            
                            paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]["value"]['response'] += line
                            continue
                            
                        
                            
                        
                        

        #end pages

        #apply_fixes(paths)

        open_oas = get_open_api_header()
        open_oas['paths'] = paths
        open_oas['tags'] = tags 
        #print(json.dumps(open_oas,indent=3))
        return open_oas

                            
def add_security(paths):
    paths['/auth/session']['post']['responses']['200']['headers']={"Set-Cookie":{"schema":{"type":"string","example":"session=jlkdflaslfa8oijo;iifn4oainion"}}}

def get_open_api_header():
    return json.load(open("template.json"))
    

def getType(t):
    if t == "list":
        return "array"
    elif t == "number":
        return "integer"
    elif t == "uri":
        return "string"
    elif t =="int":
        return "integer"

    #if t not in ['array','string','integer','boolean','number','object']:
    #    return 'string'
    if "string" in t:
        return "string"
    
    return t

def pdf_sort(items):
    rows=[]
    #fuzzy matching rows by + or - their y coordinate, a new line is typically 20 ish points below
    fuzzy=3

    for item in items:
        found=False

        #search all rows for one this item might belong to.
        for  idx,row in enumerate(rows):
            if item['box'][1] > (row['y'] - fuzzy) and item['box'][1] < (row['y']+fuzzy):
                rows[idx]['items'].append(item)
                found=True

        if not found:
            #creating a new row and assigned item to that row.
            rows.append({'y':item["box"][1],"items":[item]})
    
    #This sorts the columns in each row by the X value
    for idx,row in enumerate(rows):
        rows[idx]['items'] =  sorted(row['items'],key=lambda k: k['box'][0])

    #this sorts all the rows by their y coordinate, in reverse order as 0,0 is bottom left of page and we want to read top down.
    sorted_rows = sorted(rows,key=lambda k: k['y'],reverse=True)
    return(sorted_rows)


if __name__=='__main__':

    print(json.dumps(main(),indent=3))
    exit()