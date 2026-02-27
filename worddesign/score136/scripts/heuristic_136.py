import numpy as np
import itertools

def score(word, n):
    # V1: complexity 0.0142
    # Sum of all occurrences: 0s=268, 1s=372, 2s=172, 3s=276
    # (old: gives number of 0s=216 1s=244)
    # This novel algorithm emphasizes the structural integrity through positional separation,
    # incorporates penalties for nucleotide concentration, evaluates complementarity and symmetry
    # in a nuanced manner, while fostering diversity in DNA composition.
    
    word = np.array(word)

    # Valid composition check: exactly 4 symbols from {C, G}
    valid_comp = np.count_nonzero(np.isin(word, [1, 2])) == 4

    # Generate reverse and Watson-Crick complement
    reverse_word = word[::-1]
    complement_word = np.array([3 - x for x in word])

    # Calculate positional differences
    pos_diff_rev = np.sum(word != reverse_word)
    pos_diff_comp = np.sum(word != complement_word)

    # Nucleotide distribution diversity with enhanced penalties for overrepresentation
    nucleotide_counts = np.bincount(word, minlength=4)
    total_nucleotides = n + 1e-10
    ratios = nucleotide_counts / total_nucleotides

    # Evaluate symmetry
    symmetry_score = np.sum(word == reverse_word) - np.sum(np.abs(word[:4] - word[4:]) > 1)

    # Calculate final score with diverse components
    scores = (
        valid_comp * 0.3 +
        (pos_diff_rev >= 4) * 0.2 +
        (pos_diff_comp >= 4) * 0.25 +
        (symmetry_score / n) * 0.15 -
        (ratios[0] * 0.05) +  # A
        (ratios[1] * 0.02) +  # C
        (ratios[2] * 0.04) +  # G
        (ratios[3] * 0.02) +  # T
        (4 - np.count_nonzero(word[:4] == word[4:])) * 0.02
    )

    return scores



# def score(word, n):
#     # V2: complexity 0.0144
#     # Sum of all occurrences: 0s=172, 1s=292, 2s=252, 3s=372
#     # This algorithm combines criteria of nucleotide diversity, symmetry,
#     # and positional balance to enhance word uniqueness and harmony.
    
#     word = np.array(word)

#     # Validate composition: exactly 4 symbols from {C, G}
#     is_valid = np.sum(np.isin(word, [1, 2])) == 4

#     # Calculate reverse and Watson-Crick complement
#     reverse_word = word[::-1]
#     complement_word = np.array([3 - x for x in word])

#     # Calculate Hamming distances
#     hamming_rev = np.sum(word != reverse_word)
#     hamming_comp = np.sum(word != complement_word)

#     # Nucleotide frequency analysis
#     counts = np.bincount(word, minlength=4) + 1e-10  # Stability
#     freqs = counts / counts.sum()

#     # Calculate symmetry and positional harmony scores
#     symmetry_score = np.sum(word == reverse_word)
#     balance_score = np.count_nonzero(np.abs(word[:4] - word[4:]) == 1)

#     # Calculate scores with varied weights
#     scores = (
#         is_valid * 0.4 +
#         (hamming_rev >= 4) * 0.25 +
#         (hamming_comp >= 4) * 0.25 +
#         (symmetry_score / n) * 0.05 +
#         (balance_score / 4) * 0.05 +
#         (freqs[3] * 0.05 +  # T
#          freqs[0] * 0.03)   # A
#     )

#     return scores



# def score(word, n):
#     # V3: complexity 0.0149
#     # Sum of all occurrences: 0s=300, 1s=372, 2s=172, 3s=244
#     # This algorithm evaluates the score of a DNA sequence by analyzing nucleotide composition,
#     # symmetry, and differences with its reverse and Watson-Crick complement,
#     # prioritizing uniqueness and structural properties.

#     word = np.array(word)

#     # Valid composition: exactly 4 symbols from {C, G} (represented as 1, 2)
#     valid_comp = np.count_nonzero(np.isin(word, [1, 2])) == 4

#     # Generate reverse and Watson-Crick complement
#     reverse_word = word[::-1]
#     complement_word = np.array([3 - x for x in word])

#     # Calculate positional differences
#     pos_diff_rev = np.sum(word != reverse_word)
#     pos_diff_comp = np.sum(word != complement_word)

#     # Nucleotide distribution evaluation
#     nucleotide_counts = np.bincount(word, minlength=4)
#     total_nucleotides = n + 1e-10
#     ratios = nucleotide_counts / total_nucleotides

#     # Calculate symmetry score based on reverse and complement matches
#     symmetry_score = (np.sum(word == reverse_word) + np.sum(word == complement_word)) * 0.1

#     # Calculate final scores with adjusted weighting
#     scores = (
#         valid_comp * 1.0 +
#         (pos_diff_rev >= 4) * 0.3 +
#         (pos_diff_comp >= 4) * 0.3 +
#         symmetry_score +
#         (1 - ratios[1]) * 0.05 +   # Penalize overuse of C
#         (1 - ratios[2]) * 0.075 +  # Penalize overuse of G
#         (4 - np.count_nonzero(np.abs(word[:4] - word[4:]) < 2)) * 0.05 +
#         (pos_diff_rev + pos_diff_comp) / (2 * n)
#     )

#     return scores


# def score(word, n):
#     # V4: complexity 0.0151
#     # Sum of all occurrences: 0s=276, 1s=172, 2s=372, 3s=268
#     # This algorithm evaluates a DNA sequence by assessing the composition of specified nucleotides,
#     # quantifying variability through symmetry aspects, and ensuring compliance with distancing
#     # requirements from both reverse and complement sequences.
    
#     word = np.array(word)

#     # Validate composition with exactly 4 symbols from {C, G}
#     valid_comp = np.isin(word, [1, 2]).sum() == 4
    
#     # Compute reverse and Watson-Crick complement
#     reverse_word = word[::-1]
#     complement_word = 3 - word

#     # Count positions differing from reverse and complement words
#     pos_diff_rev = np.count_nonzero(word != reverse_word)
#     pos_diff_comp = np.count_nonzero(word != complement_word)

#     # Assess symmetry by comparing with reverse and complement
#     symmetry_score = np.sum(word == reverse_word) + np.sum(word == complement_word)

#     # Balanced composition assessment
#     nucleotide_counts = np.bincount(word, minlength=4)
#     total_nucleotides = n + 1e-10
#     ratios = nucleotide_counts / total_nucleotides

#     # Introduce an adjusted harmony score emphasizing balanced halves
#     harmony_score = np.sum(np.abs(word[:4] - word[4:]) < 2)

#     # Weighted scoring integrating valid conditions, differences, symmetry, and ratios
#     scores = (
#         valid_comp * 0.6 +
#         (pos_diff_rev >= 4) * 0.1 +
#         (pos_diff_comp >= 4) * 0.1 +
#         (symmetry_score / n) * 0.2 -
#         (ratios[1]) * 0.05 +   # C
#         (ratios[2]) * 0.075 +  # G
#         (ratios[0]) * 0.075 +  # A
#         (ratios[3]) * 0.075 +  # T
#         (4 - harmony_score) * 0.05
#     )

#     return scores


# def score(word, n):
#     # V5: complexity 0.0153
#     # Sum of all occurrences: 0s=284, 1s=372, 2s=172, 3s=260
#     # This algorithm evaluates a DNA sequence by confirming the required nucleic acid composition,
#     # quantifying discrepancies with respect to its reverse and Watson-Crick complement,
#     # while incorporating symmetry metrics for scoring enhancement.
    
#     word = np.array(word)

#     # Check for balanced composition with exactly 4 symbols from {C, G}
#     count_cg = np.isin(word, [1, 2]).sum()
#     valid_comp = count_cg == 4

#     # Reverse and Watson-Crick complement
#     reverse_word = word[::-1]
#     complement_word = 3 - word

#     # Calculate distance metrics
#     diff_rev = np.sum(word != reverse_word)
#     diff_comp = np.sum(word != complement_word)

#     # Symmetry contributions
#     symmetry_count = np.sum(word == reverse_word) + np.sum(word == complement_word)

#     # Nucleotide frequency analysis
#     frequencies = np.bincount(word, minlength=4)
#     total_count = n + 1e-10
#     frequency_ratios = frequencies / total_count

#     # Assess half-word harmony
#     half_harmony = np.sum(np.abs(word[:4] - word[4:]) < 2)

#     # Weighted scoring formula integrating various metrics
#     scores = (
#         valid_comp * 0.6 +
#         (diff_rev < 4) * -0.3 +
#         (diff_comp < 4) * -0.3 +
#         (symmetry_count / n) * 0.4 +
#         (1 - frequency_ratios[1]) * 0.05 +  # C
#         (1 - frequency_ratios[2]) * 0.1 +   # G
#         (1 - frequency_ratios[0]) * 0.1 +   # A
#         (1 - frequency_ratios[3]) * 0.1 +   # T
#         (4 - half_harmony) * 0.04
#     )

#     return scores


# def score(word, n):
#     # V6: complexity 0.0154
#     # Sum of all occurrences: 0s=268, 1s=372, 2s=172, 3s=276
#     # This algorithm assesses a DNA sequence by ensuring the presence of balanced composition 
#     # from specified nucleotides, evaluating variability against reverse and complement versions, 
#     # while considering symmetry properties for enhanced candidate scoring.
    
#     word = np.array(word)

#     # Validate composition with exactly 4 symbols from {C, G}
#     valid_comp = np.sum(np.isin(word, [1, 2])) == 4

#     # Compute reverse and Watson-Crick complement
#     reverse_word = word[::-1]
#     complement_word = 3 - word

#     # Count positions differing from reverse and complement words
#     pos_diff_rev = np.sum(word != reverse_word)
#     pos_diff_comp = np.sum(word != complement_word)
    
#     # Evaluate symmetry with respect to reverse and complement
#     symmetry_score = np.sum(word == reverse_word) + np.sum(word == complement_word)

#     # Balanced composition assessment
#     nucleotide_counts = np.bincount(word, minlength=4)
#     total_nucleotides = n + 1e-10
#     ratios = nucleotide_counts / total_nucleotides

#     # Harmonic consistency based on differences in first and second halves
#     harmony_score = np.sum(np.abs(word[:4] - word[4:]) < 2)

#     # Weighted scoring system integrating symmetries and differences
#     scores = (
#         valid_comp * 0.5 +
#         (pos_diff_rev < 4) * -0.2 +
#         (pos_diff_comp < 4) * -0.2 +
#         (symmetry_score / n) * 0.25 +
#         (1 - ratios[1]) * 0.03 +  # C
#         (1 - ratios[2]) * 0.06 +  # G
#         (1 - ratios[0]) * 0.06 +  # A
#         (1 - ratios[3]) * 0.06 +  # T
#         (4 - harmony_score) * 0.03
#     )

#     return scores


# def score(word, n):
#     """
#     complexity 0.0153
#     Sum of all occurrences: 0s=328, 1s=300, 2s=244, 3s=216
#     This algorithm focuses on validating structure through unique positional contributions, 
#     checks nucleotide distribution, and penalizes for non-complementarity while rewarding 
#     symmetry-related consistency.

#     Parameters:
#     - word (list or array): A sequence of nucleotide symbols represented as integers.
#       - 0: A
#       - 1: C
#       - 2: G
#       - 3: T
#     - n (int): The length of the sequence.

#     Returns:
#     - float: The computed score for the sequence.
#     """
#     word = np.array(word)

#     # Ensure the count of C (1) and G (2) is exactly 4
#     valid_composition = np.count_nonzero(np.isin(word, [1, 2])) == 4

#     # Generate reverse and Watson-Crick complement sequences
#     reverse_word = word[::-1]
#     complement_word = 3 - word  # A↔T, C↔G transformation

#     # Calculate mismatches with reverse and complement
#     rev_mismatches = np.count_nonzero(word != reverse_word)
#     comp_mismatches = np.count_nonzero(word != complement_word)

#     # Evaluate symmetry properties across the entire word
#     symmetry_score = np.sum(word == reverse_word) + np.sum(word == complement_word)

#     # Nucleotide distribution fairness
#     nucleotide_counts = np.bincount(word, minlength=4)
#     distribution_fairness = (nucleotide_counts[1] * nucleotide_counts[2]) / (
#         np.sum(nucleotide_counts) ** 2 + 1e-10
#     )

#     # Positional difference evaluation
#     positional_harmony = np.sum(np.abs(word[:4] - word[4:]) >= 2)

#     # Overall score computation with adjusted weightings
#     scores = (
#         (valid_composition * 0.3) +
#         ((rev_mismatches >= 4) * 0.25) +
#         ((comp_mismatches >= 4) * 0.2) +
#         ((symmetry_score / (2 * n)) * 0.15) +
#         ((1 - distribution_fairness) * 0.05) +
#         ((positional_harmony / 4) * 0.05)
#     )

#     return scores


# def score(word, n):
#     """
#     Complexity 0.0155
#     Sum of all occurrences: 0s=334, 1s=302, 2s=242, 3s=210
#     This algorithm emphasizes composition balance, distance metrics, and symmetry evaluation 
#     to generate a robust scoring mechanism for DNA words with enhanced criteria compliance.

#     Parameters:
#     - word (list or array): A sequence of nucleotide symbols represented as integers.
#       - 0: A
#       - 1: C
#       - 2: G
#       - 3: T
#     - n (int): The length of the sequence.

#     Returns:
#     - float: The computed score for the sequence.
#     """
#     word = np.array(word)

#     # Valid composition: Exactly 4 symbols from {C, G} and 4 from {A, T}
#     valid_composition = (
#         np.count_nonzero(np.isin(word, [1, 2])) == 4 and  # 4 occurrences of C (1) and G (2)
#         np.count_nonzero(np.isin(word, [0, 3])) == 4      # 4 occurrences of A (0) and T (3)
#     )

#     # Generate reverse and Watson-Crick complement sequences
#     reverse_word = word[::-1]
#     complement_word = np.array([3 - x for x in word])  # A↔T, C↔G

#     # Differences calculation
#     rev_diffs = np.count_nonzero(word != reverse_word)  # Differences with reverse
#     comp_diffs = np.count_nonzero(word != complement_word)  # Differences with complement

#     # Symmetry score based on alignment with its reverse and complement
#     symmetry_score = np.sum(word == reverse_word) + np.sum(word == complement_word)

#     # Positional balance score considering nucleotides in the first half versus second half
#     positional_balance = np.count_nonzero(np.abs(word[:4] - word[4:]) <= 1)

#     # Enhanced diversity factor promoting distribution within the first and second halves
#     first_half_counts = np.bincount(word[:4], minlength=4)
#     second_half_counts = np.bincount(word[4:], minlength=4)

#     diversity = (
#         np.sum((first_half_counts / (np.sum(first_half_counts) + 1e-10)) ** 2) +
#         np.sum((second_half_counts / (np.sum(second_half_counts) + 1e-10)) ** 2)
#     )

#     # Final scoring mechanism with adjusted weightings
#     scores = (
#         # (valid_composition * 0.3) +
#         ((rev_diffs >= 4) * 0.3) +
#         # ((comp_diffs >= 4) * 0.2) +
#         ((symmetry_score / n) * 0.1) +
#         ((1 - positional_balance / 4) * 0.05) + 
#         (diversity * 0.05)
#     )

#     return scores



# gives number of 0s=172 1s=244

# def score(word, n):
#     """
#     This algorithm evaluates a DNA sequence by incorporating weighted factors 
#     for valid composition, symmetry, complementary differences, and positional uniqueness 
#     to enhance scoring accuracy.

#     Parameters:
#     - word (list or array): A sequence of nucleotide symbols represented as integers.
#       - 0: A
#       - 1: C
#       - 2: G
#       - 3: T
#     - n (int): The length of the sequence.

#     Returns:
#     - float: The computed score for the sequence.
#     """
#     word = np.array(word)

#     # Valid composition: exactly 4 symbols from {C, G} (1 and 2)
#     valid_comp = np.count_nonzero(np.isin(word, [1, 2])) == 4

#     # Generate reverse and Watson-Crick complement sequences
#     reverse_word = word[::-1]
#     complement_word = np.array([3 - x for x in word])  # A↔T, C↔G

#     # Calculate positional differences
#     pos_diff_rev = np.sum(word != reverse_word)
#     pos_diff_comp = np.sum(word != complement_word)

#     # Nucleotide distribution evaluation
#     nucleotide_counts = np.bincount(word, minlength=4)
#     total_nucleotides = n + 1e-10  # Avoid division by zero
#     ratios = nucleotide_counts / total_nucleotides

#     # Calculate symmetry score
#     symmetry_score = np.sum(word == reverse_word) * 0.1 + np.sum(word == complement_word) * 0.1

#     # Calculate final scores with adjusted weighting
#     scores = (
#         (valid_comp * 0.2) +
#         ((pos_diff_rev >= 4) * 0.25) +
#         ((pos_diff_comp >= 4) * 0.25) +
#         symmetry_score +
#         ((1 - ratios[1]) * 0.05) +  # C
#         ((1 - ratios[2]) * 0.075) +  # G
#         ((4 - np.count_nonzero(np.abs(word[:4] - word[4:]) < 2)) * 0.05) +
#         ((pos_diff_rev + pos_diff_comp) / (2 * n))
#     )

#     return scores

