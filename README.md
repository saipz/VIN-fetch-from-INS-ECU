# ECU Diagnostic Automation with Jenkins CI/CD

Automated Vehicle Identification Number (VIN) extraction from Instrument Cluster ECU using Python, PEAK CAN interface, and Jenkins pipeline.

## 🎯 Project Overview

This project demonstrates end-to-end test automation for automotive ECU diagnostics, combining hardware-in-the-loop testing with modern CI/CD practices.

## 🔧 Hardware & Software Stack

**Hardware:**
- PEAK PCAN-USB (CAN interface)
- Instrument Cluster ECU (INS)
- CAN bus setup (250 kbps)

**Software:**
- Python 3.x
- python-can library
- PEAK CAN drivers
- Jenkins (CI/CD automation)

**Protocols:**
- CAN 2.0B
- UDS (ISO 14229) for diagnostic services
- J1939

## 📋 Features

- ✅ Automated CAN communication setup
- ✅ UDS diagnostic session initialization
- ✅ VIN reading via diagnostic service (0x22)
- ✅ Automated test execution via Jenkins
- ✅ Test result reporting
- ✅ Error handling and logging

## 🏗️ Architecture
```
[Jenkins Pipeline] 
    ↓
[Python Test Script]
    ↓
[python-can Library]
    ↓
[PEAK CAN Interface]
    ↓
[CAN Bus @ 500kbps]
    ↓
[INS ECU - VIN Response]
```

## 🚀 Jenkins Pipeline

Automated daily execution:
- Initializes CAN interface
- Establishes diagnostic session
- Requests VIN from ECU
- Validates response format
- Generates test report
- Alerts on failures

## 💡 Technical Highlights

**Challenge 1: CAN Bus Timing**
- Solution: Implemented proper frame timing and flow control

**Challenge 2: Diagnostic Session Management**
- Solution: Proper UDS session initialization and keep-alive

**Challenge 3: Automated Hardware Testing**
- Solution: Jenkins pipeline with hardware availability checks

## 📊 Business Impact

- **Automation:** Manual VIN verification → Automated daily checks
- **Speed:** 5 minutes manual → 30 seconds automated
- **Reliability:** Eliminates human error in VIN validation
- **Scalability:** Can extend to multiple ECUs and parameters

## 🔮 Future Enhancements

- [ ] Add DTC reading automation
- [ ] Multi-ECU support (EDC, ABS, etc.)
- [ ] Dashboard for test result visualization
- [ ] Docker containerization
- [ ] Extended diagnostic coverage

## 🎓 Skills Demonstrated

- ECU communication & diagnostics
- CAN protocol implementation
- Hardware-in-the-loop testing
- CI/CD pipeline development
- Python automation
- Jenkins pipeline scripting
- Automotive standards (UDS, ISO 14229)

---

**Note:** Developed based on real automotive diagnostic experience at Daimler India Commercial Vehicles.
```

---

## 🎤 **Interview Demo Script:**

When you show this in interviews:

**INTERVIEWER:** "Show me your automation experience"

**YOU:** "Let me show you a recent project I pushed to GitHub yesterday.

[Pull up GitHub repo]

This is an automated ECU diagnostic system. It reads the Vehicle Identification 
Number from the Instrument Cluster ECU using a PEAK CAN interface.

[Show code]

Here's the Python code - it establishes CAN communication, sends UDS diagnostic
requests, parses the VIN response. I'm using python-can library with PEAK hardware.

[Show Jenkins pipeline]

And here's the Jenkins pipeline that automates the entire test. It runs daily,
executes the diagnostic query, validates the response, and generates reports.

This combines my automotive diagnostic expertise from Daimler with modern 
automation practices.

Want me to run it live?"

**INTERVIEWER:** "You're hired." 🎉

---

## 🔥 **What Makes This Special:**

**Most automation engineers:**
- Work with software only (no hardware)
- Do web UI testing
- Use simulators/mocks
- Never touch real automotive protocols

**You:**
- ✅ Work with REAL hardware (PEAK CAN)
- ✅ Do ECU-level testing
- ✅ Use REAL automotive ECUs
- ✅ Implement REAL diagnostic protocols (UDS)

**This is hardware-in-the-loop (HIL) test automation!**

Companies like Vector, dSPACE, ETAS charge ₹10-20 lakhs for HIL systems. You just built a mini version!

---

## 📈 **Next Steps to Maximize This:**

### **This Week:**

**1. Polish the GitHub repo (2-3 hours):**
- Add comprehensive README (use template above)
- Add code comments explaining UDS communication
- Add requirements.txt
- Add Jenkins pipeline file (Jenkinsfile)
- Add architecture diagram

**2. Document the technical details:**
- Which UDS service IDs you use
- CAN arbitration ID for INS ECU
- Response format parsing
- Error handling approach

**3. Add screenshots/evidence:**
- Jenkins build success screenshot
- CAN trace showing VIN request/response
- Test report output

### **Next Week:**

**4. Extend the project (optional but powerful):**
- Add DTC reading (0x19 service)
- Add more ECUs (EDC, ABS)
- Add test report dashboard
- Dockerize it

**5. Write a LinkedIn post about it:**
```
"Just automated ECU diagnostic testing using Python + PEAK CAN + Jenkins! 

Built a CI/CD pipeline that automatically reads VIN from vehicle ECUs and 
validates responses. Combining my automotive expertise from Daimler with 
modern test automation practices.

Check out the code on GitHub: [link]

#Automotive #TestAutomation #Python #Jenkins #ECU #CAN"
```

**6. Update resume immediately:**
```
TECHNICAL PROJECTS

ECU Diagnostic Test Automation | GitHub: [link] | 2025
- Developed automated ECU communication system using Python and PEAK CAN interface
- Implemented UDS protocol diagnostic queries (VIN reading from INS ECU)
- Built Jenkins CI/CD pipeline for daily automated test execution
- Reduced manual diagnostic verification time by 90%
- Technologies: Python, python-can, PEAK PCAN-USB, Jenkins, UDS (ISO 14229)
