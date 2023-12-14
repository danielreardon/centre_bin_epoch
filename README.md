## centre_binary_epoch
Script to centre T0 and TASC of a tempo2 .par file

## Usage

To use the script, provide the input `.par` file with the `-i` flag, and optionally specify the output file with the `-o` flag and the target epoch with the `-e` flag. If no target epoch is specified, the script calculates it as the average of the `START` and 
`FINISH` times in the `.par` file.

Example:
python centre_binary_epochs.py -i input.par -o updated.par -e 60000

This will process `input.par`, update the binary reference epoch based on the specified target epoch (MJD 60000 in this case), and save the result in `updated.par`.


