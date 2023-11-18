# Using LLDB to See the SEXP `type` and `R_ItemDepth` values in `ReadItem()`


We are debugging R_Unserialize() and specifically ReadItem().
This reads an integer from the XDR stream and then calls UnpackFlags() to get the 
SEXP type, levels, object, attributes and tag predicate values.
When trying to understand and implement code to read this XDR stream, it is useful to see
the values of (SEXP) `type`, `hasattr`, `hastag` along with the value of `R_ReadItemDepth`.

For example, the 
```
load("i.rda")
sexp type = 2 depth = 0 hastag = 1 hasattr = 0
sexp type = 1 depth = 1 hastag = 0 hasattr = 0
sexp type = 9 depth = 2 hastag = 0 hasattr = 0
sexp type = 13 depth = 1 hastag = 0 hasattr = 1
sexp type = 2 depth = 2 hastag = 1 hasattr = 0
sexp type = 1 depth = 3 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 16 depth = 3 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 2 depth = 2 hastag = 1 hasattr = 0
sexp type = 1 depth = 3 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 16 depth = 3 hastag = 0 hasattr = 0
sexp type = 9 depth = 4 hastag = 0 hasattr = 0
sexp type = 254 depth = 2 hastag = 0 hasattr = 0
sexp type = 254 depth = 0 hastag = 0 hasattr = 0
```



## Running R under the Debugger

We assume you have a debuggable version of R.
We start it with
```sh
R -d lldb
```

### Note
Below, we use the LLDB `break command` and specify the breakpoint in each with the number 1.
We can 

+ omit this to refer to the most recently created breakpoing, or
+ specify the number of a different break point.



## The Manual Way

We can of course set a breakpoint just after the call to `UnpackFlags`, i.e., at the `switch`
statement on line 1777 of serialize.c.
Each time we stop at this point, we can interactively issue the commands
```
print type
print hasattr
print hastag
print R_ReadItemDepth
continue
```


We can use LLDB's own script language to do this with
```
break set -f serialize.c -l 1777
break command add 1 
```
This will prompt us to enter the commands in LLDB's regular scripting language.
Later we will see we can use `-s python` to use Python.


At the prompt, we enter each of these lines and end the input with DONE
```
print type
print hasattr
print hastag
print R_ReadItemDepth
continue
DONE
```

We can verify the command was set with
```
break list 
```
The text of the command should appear.

We can now return to the R process and run our `load()` command.
We get a lot of output:
```
(lldb)  print type
(SEXPTYPE) $0 = 2

(lldb)  (lldb)  print hasattr
(int) $1 = 0

(lldb)  (lldb)  print hastag
(int) $2 = 1

(lldb)  (lldb)  print R_ReadItemDepth
(int) $3 = 0

(lldb)  (lldb)  continue
Process 6649 resuming

Command #5 'continue' continued the target.
(lldb)  print type
(SEXPTYPE) $4 = 1

(lldb)  print hasattr
(int) $5 = 0

(lldb)  print hastag
(int) $6 = 0

(lldb)  print R_ReadItemDepth
(int) $7 = 1

(lldb)  continue
Process 6649 resuming
```
We see the values. 
They are not displayed in an easy to read manner.
We can do some text processing to transform them into a more convenient form.
However, we can learn more about LLDB's commands, formatting and scripting language to see if we can format the output 
better, hide the commands and the continue and 'Process ... remaining' messages.
See [here](https://lldb.llvm.org/use/variable.html)


Alternatively, we can switch to using Python and the LLDB API to which it has bindings.


## Using Python

Instead of LLDB's own scripting language, we can register Python commands to run at the breakpoint.
These commands are a mix of regular Python commands and calls to the Python [interface to LLDB](https://lldb.llvm.org/use/python.html#using-breakpoint-command-scripts).

In this example, we'll just display the value of the local variable type and the non-local/global variable
`R_ReadItemDepth`.  `hastag` and `hasattr` are just like `type` as they are local variables. So we
are dealing with both types of variables.

Our Python commands will have access to 2 variables
+ `frame`    the call frame in which the breakpoint has stopped, of class [lldb.Frame](https://lldb.llvm.org/python_api/lldb.SBFrame.html#lldb.SBFrame)
+ `bp_loc`  the break point location object, of class [https://lldb.llvm.org/python_api/lldb.SBFrame.html#lldb.SBFrame](https://lldb.llvm.org/python_api/lldb.SBBreakpointLocation.html#lldb.SBBreakpointLocation)

(Noted: There is a third variable, but it should not be used.)


### Getting the Value of a Local Variable
We'll get the variable type and then its value with `frame.FindVariable("type")` and call the
`GetValue()` method on the resulting [lldb.SBValue](https://lldb.llvm.org/python_api/lldb.SBValue.html#lldb.SBValue)
```
ty = frame.FindVariable("type").GetValue()
```

###  Getting the Value of a non-Local Variable

For a non-frame variable this, we need to search the module (file or executable?).
See [SO post](https://stackoverflow.com/questions/53331618/lldb-python-basic-print-value-of-a-global-array-while-inside-a-breakpoint-in-a)

We get the module as an attribute of the frame. We can call the module's FindFirstGlobalVariable()
method as we know there is only one variable named R_ReadItemDepth.
We pass this method 2 arguments:
+ the target program running under the debugger (i.e., R)
+ the name of the variable
```
depth = frame.module.FindFirstGlobalVariable(frame.thread.process.target, "R_ReadItemDepth").GetValue()
```
Again, we get the value of this integer variable.


### Then Entire Script
So we enter the following script:
```
break command add 1 -s python
```
We get the prompt
```
Enter your Python command(s). Type 'DONE' to end.
def function (frame, bp_loc, internal_dict):
    """frame: the lldb.SBFrame for the location at which you stopped
       bp_loc: an lldb.SBBreakpointLocation for the breakpoint location information
       internal_dict: an LLDB support object not to be used"""
```

We enter the following code.
```python
ty = frame.FindVariable("type").GetValue()
depth = frame.module.FindFirstGlobalVariable(frame.thread.process.target, "R_ReadItemDepth").GetValue()
print("sexp type = " + ty + " depth = " + depth)
return(False)
```

Our return value of  False means that the LLDB will not stop at this break point but continue.
This is the same us typing continune interactively.
Another approach is to replace the return() call with
```
frame.GetThread().GetProcess().Continue()
```
Clearly returning False is simpler.


---
**NOTE**
Your Python commands cannot contain any syntax errors. If they do, you 
 will probably get the message

```
No command attached to breakpoint.
```

after you enter the DONE command. This is frustrating.

Try the commands in a function definition in a Python session to test they are parsed correctly.

If you issue them at the Python prompt, they will be evaluated and the relevant variables and
modules are not likely to be available, leading to different errors.

---

## Using a Module

We don't want to have to enter these commands each time we set the command for the breakpoint.
Instead, we would like to tell LLDB to use an existing Python function.
We can do this by 

1. putting the function in a module
1. loading the module
1. setting the function as the command callback

### Creating the Module 

We open an empty file [sexp.py](sexp.py) and define the function
```python
def itemTypes(frame, bp_loc, dict):
   ty = frame.FindVariable("type").GetValue()
   depth = frame.module.FindFirstGlobalVariable(frame.thread.process.target, "R_ReadItemDepth").GetValue()
   print("sexp type = " + ty + " depth = " + depth + " hastag = " + frame.FindVariable("hastag").GetValue() + " hasattr = " + frame.FindVariable("hasattr").GetValue())
   frame.GetThread().GetProcess().Continue()
```
The signature is important and must be as show.


### Loading the Module


If you put this [sexp.py](sexp.py) file in a directory in which Python searches for modules,
LLDB's python will find it. If not, we will have to add the directory to the Python module path.
We can do that in LLDB's Python.
We enter the interactive python with the LLDB command `script`:
```
script
Python Interactive Interpreter. To exit, type 'quit()', 'exit()' or Ctrl-D.
```
Then we import the `sys` module and append the path to the directory containing `sexp.py`
```python
import sys
sys.path.append(r'/Users/duncan/Book/HackingREngine/RDAInfo/RDAXDR/')
```

Once Python knows how to find our module, we simply import it.
```python
import sexp
```

It is now available in the Python interpreter and we can refer to in when setting
the command callback.

## Setting the Breakpoint Command

We set the breakpoint's command to our Python function with the LLDB command
```
break comm add 1 --python-function sexp.itemTypes
```


## Using the Breakpoint Function

Now we are ready to return to the R process, call `load()` and we will
see the output at the top of this document.


## Reloading the Module

```
(lldb) script
```
```python
import importlib
importlib.reload(sexp)
```
This is all we need to do.  The next call to our breakpoint command will call
the new `sexp.itemType`. This is because 
in our call to register our Python function with  `--python-function` as the command fpr the callback,
LLDB created a wrapper function. So when this wrapper function is called, it then looks for
sexp.itemType and finds the new one.




## Collecting the Information in Python Data Structures

Rather than printing the results, we can collect the information in Python
tuples/arrays, data.frames, etc.

We use [sexp_global.py](sexp_global.py) in this  example.


In our module, we define a module-level global variable, 
```python
data = []
```

In our `itemTypes` function, instead of printing the results, we append a tuple to `data`
```python
data.append([ty, depth])
```

We load it as we did sexp.py above.
```
script
import sexp_global
```

We register the sexp_global.itemTypes as a callback command with
```
break command add 1 --python-function sexp_global.itemTypes
```


To get the results after one or more hits to this breakpoint (or other also using this function),
we drop back to LLDB and run the `script` command to enter the Python interpreter.
Then we can access the results with 
```python
sexp_global.data
```


## Resettting the Global Variable(s)

We will often want to reinitialize the data to restart the collection.
We added a `reset` method to sexp_global.py
```python
sexp_global.reset()
```

The `reset` function is defined as 
```python
def reset():
	global data
	data = []
```




# Collecting .External2 Calls

In another project, we found that a lot of time was spent in calls to .External2.
This could be many calls to one routine or to many different routines.
We cannot use `trace()` to monitor the calls to `.External2()` as it is .Primitive function.
One way to collect the names of the routines being called is using lldb.

`.External2()` maps to do_External in C code. See R_FunTab in names.c.

We wrote the python module external.py <!-- in ~/Ranswers/Heise --> below
to intercept all calls to do_External.
This evaluates the C expression 
```c
R_CHAR(STRING_ELT(Rf_deparse1s(CAR(CDR(call))), 0))
````
that we could invoke manually if we had a breakpoint on do_External, i.e., evaluating it with call **expression**.

This gets the name of the routine being invoked and increments the corresponding entry in a
dictionary, checking to see it is already there or not.

```python
import lldb

counts = {}

def update(frame, bp_loc, dict):
    options = lldb.SBExpressionOptions()
    options.SetFetchDynamicValue(True)
    pname = frame.EvaluateExpression("call R_CHAR(STRING_ELT(Rf_deparse1s(CAR(CDR(call))), 0))", options) # .GetValue()
    name = pname.GetSummary()  
    ncalls = 1
    if name in counts:
        ncalls = counts[name] + 1
    counts[name] = ncalls
    return(False)

def reset():
    global counts
    counts = {}
```

We load the module with
```
script
Python Interactive Interpreter. To exit, type 'quit()', 'exit()' or Ctrl-D.
>>> import external
>>> ^D
```

Then we set the breakpoint and then add the breakpoint command
```lldb
break set -n do_External
break command add 1 --python-function external.update
```

Then we run the code that calls .External2
```r
source("script.R")
```

At the end of this, we examine and export the dictionary so we can read it in R:
```
>>> import json
>>> json.dumps(external.counts)
'{"\\"C_termsform\\"": 12, "\\"C_modelframe\\"": 9, "\\"C_compcases\\"": 53, "\\"vctrs_new_data_frame\\"": 2951, "\\"rlang_ext_capturearginfo\\"": 1700, "\\"rlang_ext2_eval\\"": 600, "\\"rlang_ext_arg_match0\\"": 250, "\\"vctrs_type_common\\"": 100, "\\"vctrs_cast_common\\"": 100, "\\"vctrs_c\\"": 2050, "\\"vctrs_recycle_common\\"": 200, "\\"magrittr_pipe\\"": 50, "\\"rlang_ext2_call2\\"": 1000, "\\"rlang_ext_dots_values\\"": 400, "\\"rlang_ext2_exec\\"": 800, "\\"rlang_ext2_eval_tidy\\"": 50, "\\"vctrs_cbind\\"": 150, "\\"vctrs_rbind\\"": 51, "\\"C_modelmatrix\\"": 5}'
```

We write this to a file with:
```
with open('ExternalCalls.json', 'w') as outfile:
    json.dump(external.counts, outfile)
```

We can then read it into R where we are working to analyze the code.


### Issue
The external.update function causes the lldb prompt to be displayed at each call.
This causes problems with emacs as it overflows the buffer's undo ability.
Instead, we run it in a regular terminal.  We need to solve this issue.



# References

+ [LLDB Python Interface](https://lldb.llvm.org/use/python-reference.html)

+ For examples of evaluating a C expression from Python, see 
  + [external.py](~/Ranswers/Heise/) local for now.
  + [here](https://www.programcreek.com/python/example/126402/lldb.SBExpressionOptions)
