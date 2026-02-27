import ctypes
# Pre-load DLL in the SAME process before python-can loads
ctypes.windll.LoadLibrary(r"C:\Windows\System32\PCANBasic.dll")
 
# Now import and run — same process, DLL already in memory
exec(open("pycan_1.py").read())