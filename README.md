## VOS – Landing Page

This is a small React + Vite landing page for the **VOS** Windows tool.

### Run the project

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run dev
   ```
3. Open the URL shown in the terminal (by default `http://localhost:5173`).

### Configure the download button

Copy your installer to `public/downloads/vos.exe`.

The page will download it from `/downloads/vos.exe`.

### Reducing "virus", "protection", and "unknown publisher" warnings

When users download `vos.exe`, Windows (and some antivirus tools) may show warnings because the file is **unsigned** and from an **unknown publisher**. To reduce or remove these:

1. **Code-sign the .exe (recommended)**  
   Sign `vos.exe` with a **code signing certificate** from a trusted CA (e.g. DigiCert, Sectigo, SSL.com).  
   - **Standard certificate**: Removes "unknown publisher" and often reduces SmartScreen prompts after some reputation builds.  
   - **EV (Extended Validation) certificate**: Usually gets SmartScreen trust quickly and is best for downloadable apps.  
   You sign with tools like **SignTool** (Windows SDK) or **signtool.exe**; your certificate provider will give exact steps.

2. **Build reputation over time**  
   Even with a standard cert, SmartScreen may show "Windows protected your PC" for new files. As more users download and run it without issues, the warning often goes away. EV certs tend to get trusted faster.

3. **If antivirus flags the file**  
   - Ensure the .exe is signed.  
   - Submit the signed build to your antivirus vendor’s false-positive form (e.g. Microsoft Security Intelligence, VirusTotal).  
   - Avoid packing or obfuscating the exe in ways that trigger heuristic detection.

**Summary:** Signing `vos.exe` with a proper code signing certificate is the main way to address "unknown publisher" and reduce virus/protection warnings. EV certificates give the fastest SmartScreen trust for new downloads.

#### Free options

There is **no free code signing certificate** that Windows and SmartScreen trust (CAs charge for code signing). You can still do the following at no cost:

1. **Tell users how to run it**  
   On your download page, add a short note, e.g.:  
   *"If Windows SmartScreen appears: click **More info**, then **Run anyway**. The app is unsigned; this warning is normal."*  
   That doesn’t remove the warning but reduces confusion and support questions.

2. **Submit the file so AVs can whitelist it**  
   - **[VirusTotal](https://www.virustotal.com)** – Upload `vos.exe`. Many AV vendors use this to improve detection; it can help reduce false positives over time.  
   - **Microsoft** – [Submit a file](https://www.microsoft.com/en-us/wdsi/filesubmission) for analysis. If they confirm it’s clean, Defender may stop flagging it.

3. **Let reputation build**  
   Keep the same `vos.exe` (same build) when possible. As more people download and run it, SmartScreen may show the warning less often (Microsoft uses download/run telemetry). This is slow and not guaranteed.

4. **Publish in the Microsoft Store (if it fits)**  
   Store apps are signed by Microsoft, so users don’t see "unknown publisher". [Developer registration](https://developer.microsoft.com/en-us/microsoft-store/register) is free; you’d ship your app through the Store instead of (or in addition to) the direct .exe download.

