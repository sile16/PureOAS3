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


class PdfMinerWrapper(object):
    """
    Usage:
    with PdfMinerWrapper('2009t.pdf') as doc:
        for page in doc:
           #do something with the page
    """
    def __init__(self, pdf_doc, pdf_pwd=""):
        self.pdf_doc = pdf_doc
        self.pdf_pwd = pdf_pwd
 
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
        laparams = LAParams( all_texts = True)
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
            
def main():
    with PdfMinerWrapper("REST_API_1.13.pdf") as doc:
        
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
                    

                    if line.startswith("Resources") and fontname == "Arial,Bold" :
                        resource_found = True
                    
                    
                    if resource_found:
                        #count +=1
                        #i#f count > 900:
                        #    break
                        
                        
                        x_coordinate = tbox.bbox[0]
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
                            paths[path] = { method : {"tags":[tag],
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
                                                }

                            path_id = ""
                            if "{" in path:
                                path_id=path[path.find("{")+1:path.find("}")]

                            param_index=0
                            if method=="get" or method == "delete" or "{" in path:
                                paths[path][method]['parameters'] = []
                            
                            if "{" in path:
                                #adding in special path parameter volume/{volumeid}  example
                                paths[path][method]['parameters'] = [{"name":path_id,"in":"path","required":True,"schema":{"type":"string"}}]
                                param_index=1

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
                            ###paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name] = {"request":"","response":""}
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
                            if "Bold" in fontname:
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
                                        
                                if param_name == "snap":
                                    i=4

                                state = "parameters_2"

                            elif state == "parameters_2":
                                #type
                                if param_name != "None":
                                    #folders[title]['endpoints'][endpoint]['params'][param_name]['type'] = line
                                    if  method == "get" or  method == "delete":
                                        paths[path][method]['parameters'][param_index]['schema']['type']= getType(line)
                                    else:
                                        paths[path][method]['requestBody']['content']['application/json']['schema']['properties'][param_name]['type'] = getType(line)

                                state = "parameters_3"
                                middle_x = x_coordinate

                            elif state == "parameters_3":
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


                        elif state.startswith("example_request"):
                            if state == "example_request":
                                #split = line.split()
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['method'] = split[0]
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['url'] = split[1]
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['body'] = ""
                                
                                ###paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]['request'] += line
                                continue
                                
                                #paths[path][method]["responses"]["200"]['examples'][example_name]['request'] += line
                                state="example_request_2"
                            else:
                                #folders[title]['endpoints'][endpoint]['examples'][example_name]['body'] += line
                                #paths[path][method]["responses"]["200"]['examples'][example_name]['request'] += line
                                ###paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]['request'] += line
                                continue
                            

                        elif state == "example_response":
                            #folders[title]['endpoints'][endpoint]['examples'][example_name]['response'] += line
                            #paths[path][method]["responses"]["200"]['examples'][example_name]['response'] += line
                            
                            ###paths[path][method]["responses"]["200"]["content"]["application/json"]["examples"][example_name]['response'] += line
                            continue
                        
                            


                                
                            

                            

                        


                    
                        

                        


                        
                        

        #end pages

        #apply_fixes(paths)

        open_oas = get_open_api_header()
        open_oas['paths'] = paths
        open_oas['tags'] = tags 
        print(json.dumps(open_oas,indent=3))

                            
def add_security(paths):
    paths['/auth/session']['post']['responses']['200']['headers']={"Set-Cookie":{"schema":{"type":"string","example":"session=jlkdflaslfa8oijo;iifn4oainion"}}}

                             
                    
                        

def get_open_api_header():
    return {
    "openapi": "3.0.1",
    "info": {
        "title": "Pure FlashArray API",
        "description": "# Introduction\nPure FlashArray API\n\n# Overview\nUse an API-Token to start a session, that returns an session cookie which expires in 30 minutes by default.\n\n# Authentication\nWhat is the preferred way of using the API?\n\n# Error Codes\nUse HTTP Response codes to determine command results.  Error message json formats can be different depending on the API Call. Use the CORS Everywhere FireFox extension to use this tool.",
        "version": "1.13 (definition version 0.1)"
    },
    "servers": [
        {
            "url": "https://{hostname}/api/{APIVersion}/",
            "variables": {
                "hostname": {
                    "description": "The dns FQDN or IP of the array",
                    "default": "change-me"
                },
                "APIVersion": {
                    "description": "",
                    "default": "1.13"
                }
            }
        },
        {
            "url": "https://{hostname}/api/",
            "description":"Used ONLY for GET /api_version",
            "variables": {
                "hostname": {
                    "description": "The dns FQDN or IP of the array",
                    "default": "change-me2"
                }
                
            }
        }
    ],
    "security":
     [
         {"cookieAuth":[]}
     ],
     "components": {
         "securitySchemes":{
             "cookieAuth":{
                 "type": "apiKey",
                 "in": "cookie",
                 "name":"session"
             }
         }
     }
    }
    


def getType(t):
    if t == "list":
        return "array"
    elif t == "number":
        return "integer"
    elif t == "uri":
        return "string"

    if t not in ['array','string','integer','boolean','number','object']:
        return 'string'
    
    return t
                                
                
 
if __name__=='__main__':
    main()