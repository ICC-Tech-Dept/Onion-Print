import re

pdf = "my.pdf"  
  
rxcountpages = re.compile(r"/Type\s*/Page([^s]|$)", re.MULTILINE|re.DOTALL)  
  
def countPages(filename):  
    data = file(filename,"rb").read().decode('utf-8', 'ignore') 
    return len(rxcountpages.findall(data))
  
if __name__=="__main__":  
    print("Number of pages in PDF File:", countPages(pdf))
