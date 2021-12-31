def itemTypes(frame, bp_loc, dict):
   ty = frame.FindVariable("type").GetValue()
   depth = frame.module.FindFirstGlobalVariable(frame.thread.process.target, "R_ReadItemDepth").GetValue()
   print("sexp type = " + ty + " depth = " + depth + " hastag = " + frame.FindVariable("hastag").GetValue() + " hasattr = " + frame.FindVariable("hasattr").GetValue())
   # frame.GetThread().GetProcess().Continue()
   return(False)

