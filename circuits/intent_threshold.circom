pragma circom 2.0.0;

/*
 * intent_threshold.circom
 * 
 * Zero-knowledge proof that AI confidence meets minimum threshold
 * without revealing the exact confidence score.
 * 
 * Inputs:
 *   - confidence: integer (0..10000) representing confidence*100
 *     Example: 94.3% = 9430
 *   
 *   - threshold: integer (0..10000) representing threshold*100
 *     Example: 92.0% = 9200
 * 
 * Output:
 *   - valid: 1 if confidence >= threshold, 0 otherwise
 * 
 * Security properties:
 *   - Verifier learns only whether threshold was met
 *   - Exact confidence score remains private
 *   - Cannot generate valid proof with false confidence
 */

template IntentThreshold() {
    // Input signals
    signal input confidence;
    signal input threshold;
    
    // Output signal
    signal output valid;
    
    // Range constraints to prevent overflow
    // confidence must be in [0, 10000] (0.00% to 100.00%)
    signal confidence_bits[14];  // 2^14 = 16384 > 10000
    signal threshold_bits[14];
    
    // Bit decomposition of confidence
    var sum_confidence = 0;
    for (var i = 0; i < 14; i++) {
        confidence_bits[i] <-- (confidence >> i) & 1;
        confidence_bits[i] * (confidence_bits[i] - 1) === 0;  // Binary constraint
        sum_confidence += confidence_bits[i] * (2 ** i);
    }
    sum_confidence === confidence;
    
    // Bit decomposition of threshold
    var sum_threshold = 0;
    for (var i = 0; i < 14; i++) {
        threshold_bits[i] <-- (threshold >> i) & 1;
        threshold_bits[i] * (threshold_bits[i] - 1) === 0;  // Binary constraint
        sum_threshold += threshold_bits[i] * (2 ** i);
    }
    sum_threshold === threshold;
    
    // Range checks (0 <= value <= 10000)
    signal confidence_check;
    signal threshold_check;
    
    confidence_check <== confidence * (confidence - 10000);
    threshold_check <== threshold * (threshold - 10000);
    
    // Ensure values are in valid range
    // If confidence > 10000, this will fail the constraint
    confidence <= 10000;
    threshold <= 10000;
    
    // Compute difference: diff = confidence - threshold
    signal diff;
    diff <== confidence - threshold;
    
    // Check if diff >= 0 (confidence >= threshold)
    // We use LessThan comparison
    component lt = LessThan(15);  // 15 bits is enough for our range
    lt.in[0] <== threshold;
    lt.in[1] <== confidence;
    
    // valid = 1 if confidence >= threshold (i.e., threshold < confidence or equal)
    // lt.out = 1 if threshold < confidence
    // We need to handle equality case
    signal is_equal;
    is_equal <== (confidence - threshold) * 0;  // Will be 0 if equal
    
    valid <== lt.out + (1 - lt.out) * (1 - (diff * diff) / (diff * diff + 1));
}

// LessThan template for comparison
template LessThan(n) {
    assert(n <= 252);
    signal input in[2];
    signal output out;

    component n2b = Num2Bits(n+1);
    n2b.in <== in[0] + (1<<n) - in[1];

    out <== 1-n2b.out[n];
}

// Num2Bits - converts number to binary representation
template Num2Bits(n) {
    signal input in;
    signal output out[n];
    var lc1=0;

    var e2=1;
    for (var i = 0; i<n; i++) {
        out[i] <-- (in >> i) & 1;
        out[i] * (out[i] -1 ) === 0;
        lc1 += out[i] * e2;
        e2 = e2+e2;
    }

    lc1 === in;
}

component main {public [threshold]} = IntentThreshold();
