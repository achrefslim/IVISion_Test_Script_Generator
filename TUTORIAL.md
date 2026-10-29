# Tutorial: using the IVISion Test Script Generator

This guide shows how to install the application, generate a test script from a wiring list, compare two versions of a list, and build a Windows executable.

## Part 1: Installation

**Step 1.** Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). On Windows, tick **Add Python to PATH** during the installation.

**Step 2.** Download the project:

```bash
git clone https://github.com/achrefslim/IVISion_Test_Script_Generator.git
cd IVISion_Test_Script_Generator
```

**Step 3.** (Recommended) create a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

On Linux or macOS use `source venv/bin/activate`.

**Step 4.** Install the packages:

```bash
pip install -r requirements.txt
```

**Step 5 (only for scanned PDFs).** The OCR needs two external programs:

1. **Tesseract OCR**: on Windows install it from the [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki) and add its folder to the PATH.
2. **Poppler**: download it for Windows from [poppler windows releases](https://github.com/oschwartz10612/poppler-windows/releases), unzip it and add its `bin` folder to the PATH.

Excel files and PDFs that contain real text do not need these two programs.

## Part 2: Start the application

```bash
python main.py
```

The home window opens with two buttons:

| Button | Tool |
|---|---|
| **Muster** | Script generator |
| **Compare Excel Files** | Comparison tool |

## Part 3: Generate a test script

**Step 1.** Click **Muster**.

**Step 2.** Choose the input file. Drag and drop an Excel or PDF file on the window, or click **Browse**. To try it, use `samples/sample_wiring_list.xlsx`.

**Step 3.** Choose the column mode (Excel only):

| Mode | When to use it |
|---|---|
| **Auto detect columns** | The list uses one of the supported layouts (see the README). This works for most files |
| **Manual columns** | Your file has other column names. Choose 2 or 4 columns and type their exact names |

With **Manual columns** and 4 columns, give them in this order: from device, from pin, to device, to pin. With 2 columns, give the start column and the end column, each cell containing a full address like `X1:2` or `X1/2`.

**Step 4.** Choose where to save the result with the **Browse** button of **Output IVS file**, for example `my_harness.ivs`.

**Step 5.** Click **Generate IVISion Script**. A window asks for the target version:

| Version | Output |
|---|---|
| **IVISion Studio** | `TestNetwork` and `TestConnection` commands, followed by the isolation test, the unplug test and the operator prompts |
| **IVISion 3** | `CONNECTION` commands inside `DefSec( Section1 );` |

**Step 6.** Read the **Generation Log**. A green message confirms the file was created. Errors are shown in red with the reason.

**Step 7.** Open the `.ivs` file and check it, especially the lines starting with `//===>` (for example the reminder about resistors). Then load it into the IVISion software.

Use **Reset** to clear the form and **Back** to return to the home window.

## Part 4: Understanding the generated script

| Line | Meaning |
|---|---|
| `TestNetwork( 'SP1', Topology= STAR, "K1/A1", "X1/1", "X2/3" );` | All these points are joined by splice SP1 and must be connected together |
| `TestNetwork( 'SP2-SP3', ... )` | SP2 and SP3 are connected, so they form one bigger network |
| `TestConnection( "X1/3", "X2/4" );` | A simple wire between two points |
| `//===> Vérifier si ( R1 ) sont des resistances` | Reminder to check whether R1 is a resistor and to add its resistance test |
| `DoIsolationTest();` | Checks that no unwanted connection exists |
| `DoUnplugTest();` | Asks the operator to unplug the harness and checks it |
| `UIMessageSetVariable('FA', ...)` and `('OP-ID', ...)` | Ask for the order number and the operator ID |

Address formats are cleaned automatically, for example:

| In the wiring list | In the script |
|---|---|
| `X1:2` | `X1/2` |
| `=+A-X1:2` (with a location prefix) | `X1/2` |
| `X1/2:3` | `X1.2/3` |
| `X1:2:3` | `X1/2` |

## Part 5: Compare two versions

**Step 1.** On the home window click **Compare Excel Files**.

**Step 2.** Select the old version with **Browse File 1** and the new version with **Browse File 2**.

**Step 3.** Choose the mode in the list:

| Mode | Files expected | Result |
|---|---|---|
| **Compare Connection** | Two wiring lists (same formats as the generator) | Added connections and removed connections |
| **Compare Material** | Two material lists with 3 columns and no header: name, quantity, reference | Parts added, removed, or modified (quantity or reference) |

**Step 4.** Click **Compare** and read the report.

Try it with the samples:

1. `samples/sample_wiring_list.xlsx` and `samples/sample_wiring_list_v2.xlsx` in **Compare Connection** mode: one connection added, two removed.
2. `samples/sample_material_list.xlsx` and `samples/sample_material_list_v2.xlsx` in **Compare Material** mode: one part added, one removed, two modified.

## Part 6: Use the generators from Python

You can also call the functions directly, for example in a batch script:

```python
from ivs_generator import generate_complete_ivs_script
from ivs3_generator import generate_ivs3_from_excel_or_pdf
from compare_logic import compare_excels

print(generate_complete_ivs_script("samples/sample_wiring_list.xlsx", "out_studio.ivs"))
print(generate_ivs3_from_excel_or_pdf("samples/sample_wiring_list.xlsx", "out_ivs3.ivs"))
print(compare_excels("samples/sample_wiring_list.xlsx", "samples/sample_wiring_list_v2.xlsx"))
```

To force specific columns, pass `manual_columns`, for example `["from Device", "from Pin", "to Device", "to Pin"]`.

## Part 7: Build a Windows executable

**Step 1.** Install PyInstaller:

```bash
pip install pyinstaller
```

**Step 2.** Build a single file application with its icon and images:

```bash
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --add-data "logo.png;." --name IVISionTools main.py
```

**Step 3.** The program is created in `dist\IVISionTools.exe`. Keep `icon.ico` and `logo.png` next to it if the images do not appear.

## Part 8: Troubleshooting

| Problem | Solution |
|---|---|
| `No valid connections found` | The columns were not recognised. Use **Manual columns** and type the exact column names |
| `Invalid number of manual columns` | Manual mode needs exactly 2 or 4 columns |
| Error with a scanned PDF | Install Tesseract and Poppler and add them to the PATH (Part 1 step 5) |
| A PDF gives very few connections | The diagram text may be an image of low quality. Export the wiring list to Excel from your CAD software instead |
| Logo or icon missing | Start the program from the project folder so `logo.png` and `icon.ico` are found |
| `ModuleNotFoundError` | Activate the virtual environment and run `pip install -r requirements.txt` again |
