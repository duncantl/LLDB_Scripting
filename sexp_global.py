data = []

def itemTypes(frame, bp_loc, dict):
   ty = frame.FindVariable("type").GetValue()
   depth = frame.module.FindFirstGlobalVariable(frame.thread.process.target, "R_ReadItemDepth").GetValue()
   data.append([ty, depth])
   return(False)

def reset():
   global data
   data = []

