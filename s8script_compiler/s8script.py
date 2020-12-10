#!/usr/bin/python

import sys

"""
Dette programmet tillater brukeren å lage SLEDE-8 programmer igjennom
et enkelt scripting-språk. 

ADVARSEL: Lite pen python-kode
"""

header_start = """
HOPP main

; built-in functions
"""
header_end = """

; main function
main:
"""

def gen_print(var):
	return """
TUR print
FINN $
TUR print_loop
	""".replace("$",var)


standard_libary = {
"print":"""
print:
SETT r0, 0x00
SETT r1, 0x00
SETT r2, 0x00
SETT r3, 0x00
SETT r4, 0x01
SETT r5, 0x00
RETUR
print_loop:
LAST r2
SKRIV r2
PLUSS r0, r4
ULIK r2, r5
BHOPP print_loop
RETUR
""",
"multiply":"""
multiply:
SETT r2, r1
SETT r3, 0x01
SETT r4, 0x00
SETT r5, 0x00
multiply_loop:
MINUS r2, r3
PLUSS r5, r0
ULIK r2, r5
BHOPP multiply_loop
RETUR
"""
}

def gen_data(name,content):
	res = ""
	res += name+":\n.DATA "
	res += ",".join([hex(ord(i)) for i in content[1:-1]])
	res += ",0x00\n"
	return res

opchars = "+-="
operations = ["+","-","^","&","|","<<",">>"]
op_aliases = ["PLUSS","MINUS","OG","ELLER","VSKIFT","HSKIFT"]
op_dict = {i:j for i,j  in zip(operations,op_aliases)}
def eval2(exp,integers,reg):
	res = ""
	_exp = ["+"]+exp
	for i in range(0,len(_exp),2):
		if not _exp[i+1] in integers:
			if _exp[i+1]=="$input":
				res+="LES r0\n"
			else:
				res+=f"SETT r0, {_exp[i+1]} \n"
		res+=f"{op_dict[_exp[i]]} {reg}, {integers[_exp[i+1]] if _exp[i+1] in integers else 'r0'}\n"
	return res
boolean_operations = ["==","!=","<","<=",">",">="]
boolop_aliases = ["LIK","ULIK","ME","MEL","SE","SEL"]
boolop_dict = {i:j for i,j  in zip(boolean_operations,boolop_aliases)}
boolinv = {
	"LIK":"ULIK",
	"ULIK":"LIK",
	"ME":"SEL",
	"MEL":"SE",
	"SE":"MEL",
	"SEL":"ME"
}
def evalBoolean(exp,integers,dest,inverse=False):
	if len(exp)==1:
		if (exp[0]=="true") != inverse:
			return f"\nHOPP {dest}\n"
		elif (exp[0]=="false") != inverse:
			return f"\nNOPE\n"
	res = ""
	op = ""
	iexp1 = []
	iexp2 = []
	ie1l = 0
	for i in exp:
		if i in boolean_operations:
			op = boolop_dict[i]
			break
		iexp1.append(i)
		ie1l+=1
	for i in exp[ie1l+1:]:
		iexp2.append(i)
	res += "SETT r2, 0\n"
	res += "SETT r3, 0\n"
	res += eval2(iexp1,integers,"r2")+"\n"
	res += eval2(iexp2,integers,"r3")+"\n"
	if inverse:
		op = boolinv[op]
	res += f"{op} r2,r3\n" 
	res += f"BHOPP {dest}\n"
	return res

def print_int(exp,integers):
	res="SETT r1, 0\n"
	res+=eval2(exp,integers,"r1")
	res+="\nSKRIV r1\n"
	return res
def compile(inp):
	lines = inp.split("\n")
	available_registers = ["r"+str(i) for i in range(5,16)]
	occupied_registers = ["r"+str(i) for i in range(0,6)]
	integers = {}
	strings = {}
	header = header_start
	code = ""
	data = ""
	bracketClose = []
	#print("Lines:")
	#print(lines)
	stringCount = 0
	whileCount = 0
	ifCount = 0
	for l in lines:
		i = l.strip()
		if i.replace(" ","")=="":
			continue
		#code+=f"; {i}\n"
		tokens = []
		buf = ""
		isString = False
		isOperator = False
		for j in i:
			if j=='"':
				isString = not isString

			elif j==" " and not isString:
				if buf!="": tokens.append(buf)
				buf = ""
				continue
			elif j==";" and not isString:
				if buf!="": tokens.append(buf)
				buf = ""
				buf+= j
				break
			elif j=="{" and not isString:
				tokens.append(buf+"{")
				break
			elif j in opchars:
				isOperator= True
			elif isOperator:
				if buf!="": tokens.append(buf)
				buf = ""
				isOperator= False
			elif j=="}":
				tokens = ["}"]
				break;
				
			buf+= j
		#print("Tokens:")
		#print(tokens)
		if tokens[0]=="using":
			if len(tokens)==2:
				header += standard_libary[tokens[1]]
		elif tokens[0]=="string":
			if len(tokens)==4 and tokens[2]=="=":
				if tokens[3][0]=='"':
					data += gen_data(tokens[1],tokens[3])
					strings[tokens[1]] = "data"
				elif tokens[3][0]=="$input":
					strings[tokens[1]] = "input"
		elif tokens[0]=="int":
			reg = available_registers[-1]
			available_registers.pop(-1)
			occupied_registers.append(reg)
			code += f"\nSETT {reg}, 0\n"

			integers[tokens[1]]=reg
			if len(tokens)>3 and tokens[2]=="=":
				code+= eval2(tokens[3:],integers,reg)
		elif tokens[0]=="print":
			if len(tokens)==2:
				if tokens[1][0]=='"':
					data += gen_data("string"+str(stringCount),tokens[1])
					code += gen_print("string"+str(stringCount))
					stringCount+=1
				elif tokens[1] in strings.keys() and strings[tokens[1]]=="data":
					code+=gen_print(tokens[1])
				else:
					code+= print_int(tokens[1:],integers)
			else:
				code+= print_int(tokens[1:],integers)
		elif tokens[0]=="while":
			if tokens[-1]=="{":
				code+=f"\nwhile{str(whileCount)}:\n"
				bracketClose.append(evalBoolean(tokens[1:-1],integers,f"while{str(whileCount)}"))
				whileCount+=1
		elif tokens[0]=="if":
			if tokens[-1]=="{":
				code+=evalBoolean(tokens[1:-1],integers,f"if{str(ifCount)}",inverse=True)
				bracketClose.append(f"\nif{str(ifCount)}:\n")
				ifCount+=1
		elif tokens[0]=="}":
			code += "\n"+bracketClose[-1]
			bracketClose.pop(-1)
		elif tokens[0] in integers.keys():
			if len(tokens)==2:
				code+=f"SETT r0, 1\n"
				if tokens[1]=="++":
					code+=f"PLUSS {integers[tokens[0]]}, r1\n"
				elif tokens[1]=="--":
					code+=f"MINUS {integers[tokens[0]]}, r1\n"
			elif len(tokens)>2:
				code+=f"SETT r1, 0\n"
				if tokens[1]=="=":
					code+=f"SETT r1, {integers[tokens[0]]}\n"
					code+=f"SETT {integers[tokens[0]]}, 0\n"
					code+= eval2(tokens[2:],integers,"r1")
					code+=f"SETT {integers[tokens[0]]}, r1\n"
				elif tokens[1]=="+=":
					code+= eval2(tokens[2:],integers,"r1")
					code+=f"PLUSS {integers[tokens[0]]}, r1\n"
				elif tokens[1]=="-=":
					code+= eval2(tokens[2:],integers,"r1")
					code+=f"MINUS {integers[tokens[0]]}, r1\n"

	#print("\n\nCompiled result:\n\n")
	header+=header_end
	code += "\nSTOPP\n"
	return header+code+"\n\n"+data

c = open(sys.argv[1],"r")
d = open(sys.argv[2],"w+")
d.write(compile(c.read()))
c.close()
d.close()
