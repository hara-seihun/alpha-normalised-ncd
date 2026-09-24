# Bibliography

1. Ming Li, Xin Chen, Xin Li, Bin Ma, and Paul M. B. Vitányi. 2004. **The Similarity Metric.** *IEEE Transactions on Information Theory* 50(12), 3250–3264. [doi:10.1109/TIT.2004.838101](https://doi.org/10.1109/TIT.2004.838101). [Author PDF](https://homepages.cwi.nl/~paulv/papers/similarity.pdf). Foundational normalized information distance and its compression approximation; theoretical properties of NID do not automatically transfer to a particular compressor or lossy source representation.

2. Rudi Cilibrasi and Paul M. B. Vitányi. 2005. **Clustering by Compression.** *IEEE Transactions on Information Theory* 51(4), 1523–1545. [doi:10.1109/TIT.2005.844059](https://doi.org/10.1109/TIT.2005.844059). [Corrected author version](https://homepages.cwi.nl/~paulv/papers/cluster.pdf). Defines and applies practical NCD; motivates careful treatment of compressor properties and compressed lengths.

3. Brenda S. Baker. 1995. **On Finding Duplication and Near-Duplication in Large Software Systems.** *Proceedings of the Second Working Conference on Reverse Engineering*, 86–95. [doi:10.1109/WCRE.1995.514697](https://doi.org/10.1109/WCRE.1995.514697). Established clone detection under systematic substitution of identifiers and constants, with reengineering applications.

4. Earl T. Barr, Mark Harman, Phil McMinn, Muzammil Shahbaz, and Shin Yoo. 2015. **The Oracle Problem in Software Testing: A Survey.** *IEEE Transactions on Software Engineering* 41(5), 507–525. [doi:10.1109/TSE.2014.2372785](https://doi.org/10.1109/TSE.2014.2372785). [Author PDF](https://philmcminn.com/publications/barr2015.pdf). Separates producing test inputs from deciding whether observed behaviour is correct, and surveys sources of oracles.

5. Huai Liu, Fei-Ching Kuo, Dave Towey, and Tsong Yueh Chen. 2014. **How Effectively Does Metamorphic Testing Alleviate the Oracle Problem?** *IEEE Transactions on Software Engineering* 40(1), 4–22. [doi:10.1109/TSE.2013.46](https://doi.org/10.1109/TSE.2013.46). [Author manuscript](https://vuir.vu.edu.au/33046/1/TSEmt.pdf). Studies specification relations across executions as partial oracles; distinct-looking test syntax does not necessarily imply distinct relations.

6. Yue Jia and Mark Harman. 2011. **An Analysis and Survey of the Development of Mutation Testing.** *IEEE Transactions on Software Engineering* 37(5), 649–678. [doi:10.1109/TSE.2010.62](https://doi.org/10.1109/TSE.2010.62). Reviews fault-based assessment through introduced program changes and test discrimination.

7. Robert Feldt, Richard Torkar, Tony Gorschek, and Wasif Afzal. 2008. **Searching for Cognitively Diverse Tests: Towards Universal Test Diversity Metrics.** *ICST Workshops*. [doi:10.1109/ICSTW.2008.36](https://doi.org/10.1109/ICSTW.2008.36). [Author PDF](https://www.cse.chalmers.se/~feldt/publications/feldt_2008_sbst_universal_test_diversity.pdf). Proposes NCD-based test diversity and compares it with human test clustering.

8. Robert Feldt, Simon Poulding, David Clark, and Shin Yoo. 2016. **Test Set Diameter: Quantifying the Diversity of Sets of Test Cases.** *ICST*, 223–233. [doi:10.1109/ICST.2016.33](https://doi.org/10.1109/ICST.2016.33). [Paper](https://coinse.github.io/publications/pdfs/Feldt2016if.pdf). Extends compression-derived diversity to multisets and evaluates test selection on four systems.

9. Takashi Ishio, Naoto Maeda, Kensuke Shibuya, and Katsuro Inoue. 2018. **Cloned Buggy Code Detection in Practice Using Normalized Compression Distance.** *ICSME*, 148–151. [doi:10.1109/ICSME.2018.00022](https://doi.org/10.1109/ICSME.2018.00022). [Author PDF](https://sel.ist.osaka-u.ac.jp/lab-db/betuzuri/archive/1131/1131.pdf). Applies NCD to retrieval of clones of known faulty code in industrial use.

10. Islam T. Elgendy, Robert M. Hierons, and Phil McMinn. 2024. **Evaluating String Distance Metrics for Reducing Automatically Generated Test Suites.** *AST*, 171–181. [doi:10.1145/3644032.3644455](https://doi.org/10.1145/3644032.3644455). [Author PDF](https://philmcminn.com/publications/elgendy2024.pdf). Directly compares textual test-source distances, including NCD, for suite reduction and evaluates mutation-score retention.

These works establish the component techniques and prior applications. This note's focus is the combined alpha-normalised review workflow and its distinction between structural overlap and independently sourced behavioural evidence.
