# Biological Paper Parsing Prompt

Extract the content from a biological research paper page and output in Markdown syntax. Enclose the content in the <markdown></markdown> tag and do not use code blocks. If the image is empty then output a <markdown></markdown> without anything in it.

Follow these steps:

1. Examine the provided page carefully, paying special attention to biological and chemical content.

2. Identify all elements present in the page, including:
   - Headers, body text, footnotes, tables, images, captions, and page numbers
   - Chemical structures and molecular diagrams
   - Protein structures and biological pathways
   - SMILES codes, InChI strings, and other chemical identifiers
   - Experimental data tables and bioactivity measurements
   - Phylogenetic trees and sequence alignments

3. Use markdown syntax to format your output:
   - Headings: # for main, ## for sections, ### for subsections, etc.
   - Lists: * or - for bulleted, 1. 2. 3. for numbered
   - Do not repeat yourself

4. If the element is an image (not table):
   - If the information in the image can be represented by a table, generate the table containing the information of the image
   - Otherwise provide a detailed description about the information in image
   - For biological content, classify the element as one of: 
     * Chemical Structure, Protein Structure, Pathway Diagram, Phylogenetic Tree, 
     * Gel Electrophoresis, Microscopy Image, Graph/Chart, Sequence Alignment, 
     * Molecular Interaction, Experimental Setup, Other
   - Enclose the class in <figure_type></figure_type>
   - For chemical structures, include:
     * Molecular formula if visible
     * SMILES code if provided
     * Chemical name or identifier
     * Any stereochemistry information
   - For protein structures, include:
     * Protein name and PDB ID if available
     * Secondary structure elements (α-helices, β-sheets)
     * Active sites or binding pockets
     * Ligand interactions if shown
   - Enclose <figure_type></figure_type>, the table or description, and the figure title or caption (if available), in <figure></figure> tags
   - Do not transcribe text in the image after providing the table or description

5. If the element is a table:
   - Create a markdown table, ensuring every row has the same number of columns
   - Maintain cell alignment as closely as possible
   - Do not split a table into multiple tables
   - For biological data tables, pay special attention to:
     * IC50, EC50, Ki values and their units (nM, μM, etc.)
     * Protein names and gene symbols
     * Chemical compound names and identifiers (ChEMBL ID, PubChem CID)
     * Statistical significance values (p-values, confidence intervals)
     * Experimental conditions (pH, temperature, concentration)
   - If a merged cell spans multiple rows or columns, place the text in the top-left cell and output ' ' for other cells
   - Use | for column separators, |-|-| for header row separators
   - If a cell has multiple items, list them in separate rows
   - If the table contains sub-headers, separate the sub-headers from the headers in another row

6. If the element is a paragraph:
   - Transcribe each text element precisely as it appears
   - Pay special attention to:
     * Chemical names and preserve exact spelling
     * Protein names and gene symbols (maintain capitalization)
     * SMILES codes and chemical identifiers
     * Numerical values with proper units
     * Statistical data and experimental parameters

7. If the element is a header, footer, footnote, page number:
   - Transcribe each text element precisely as it appears

8. Special handling for biological content:
   - Preserve chemical nomenclature exactly as written
   - Maintain proper formatting for gene names (italics) and protein names
   - Include any chemical identifiers (CAS numbers, ChEMBL IDs, etc.)
   - Preserve units for all measurements
   - Note any experimental conditions or methodological details

Output Example:
<markdown>
<figure>
<figure_type>Chemical Structure</figure_type>
Figure 2: Structure of Aspirin (acetylsalicylic acid)
Chemical structure showing aspirin with molecular formula C9H8O4. The structure displays a benzene ring with a carboxylic acid group and an acetyl ester group. SMILES: CC(=O)OC1=CC=CC=C1C(=O)O
</figure>

<figure>
<figure_type>Graph/Chart</figure_type>
Figure 3: Dose-response curve for compound inhibition of HER2 kinase activity
| Concentration (nM) | % Inhibition | IC50 (nM) |
|-|-|-|
| 1 | 15.2 ± 2.1 | |
| 10 | 45.8 ± 3.4 | |
| 100 | 78.9 ± 1.8 | 25.4 ± 2.7 |
| 1000 | 95.1 ± 0.9 | |
</figure>

# Targeting HER2 with Novel Small Molecule Inhibitors

## Chemical Synthesis and Characterization

The target compound **3a** (ChEMBL ID: CHEMBL123456) was synthesized according to the following procedure. The final product showed high purity (>95%) by HPLC analysis.

<figure>
<figure_type>Protein Structure</figure_type>
Figure 1: Crystal structure of HER2 kinase domain in complex with inhibitor
Protein structure showing HER2 kinase domain (PDB ID: 3PP0) with bound inhibitor in the ATP-binding pocket. Key residues Lys753 and Asp863 are highlighted. The inhibitor forms hydrogen bonds with the hinge region.
</figure>

## Biological Activity

| Compound | HER2 IC50 (nM) | EGFR IC50 (nM) | Selectivity |
|-|-|-|-|
| **3a** | 12.5 ± 1.2 | 245 ± 18 | 19.6 |
| **3b** | 8.9 ± 0.8 | 156 ± 12 | 17.5 |
| Lapatinib | 15.2 ± 2.1 | 10.8 ± 1.5 | 0.7 |

* All values represent mean ± SEM (n=3)
* Statistical significance determined by Student's t-test (p < 0.05)

</markdown>
