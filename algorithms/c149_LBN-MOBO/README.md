# LBN-MOBO



## Getting started

To run a demonstration of LBN-MOBO on the ZDT3 problem, follow these steps:

1. Download the repository az a zip file and extract it in a folder named  **lbn_mobo-main**  on your Google Drive. Make sure to extract this folder at the root level of your Google Drive. The the path in the code is set accordingly.

2. Open the 'LBN-MOBO.ipynb' file in Google Colab and run it.

By following these steps, you can easily execute the code on Google Colab and explore the demonstration of LBN-MOBO on the 30 dimension ZDT3 problem. You can change the number of iterations and batchsize using 'iter_max', and 'Batch_size' respectively.

Please be aware that the computation time for the entire process on a CPU in Google Colab is approximately 1.6 hours. However, in real-world scenarios, we perform training of networks and acquisition computations in parallel using a cluster of GPUs and CPUs. 

We have provided code examples for parallel computation in the 'Parallel_computing/Airfoil_design', 'Parallel_computing/ZDT3', and 'Parallel_computing/Printer_Gamut' folders. However, it's important to note that these examples are tailored to specific systems and would require adjustments to be useful on different hardware configurations.
