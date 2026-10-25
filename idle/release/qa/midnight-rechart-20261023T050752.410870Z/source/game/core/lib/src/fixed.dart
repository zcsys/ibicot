/// A deterministic 24-decimal fixed-point value. Currency ledgers are separate
/// integer micro-R amounts; this type describes rates and multipliers.
class Fixed implements Comparable<Fixed> {
  static final BigInt scale = BigInt.from(10).pow(24);
  static final Fixed zero = Fixed.raw(BigInt.zero);
  static final Fixed one = Fixed.raw(scale);
  final BigInt raw;

  Fixed.raw(this.raw);
  factory Fixed.integer(int value) => Fixed.raw(BigInt.from(value) * scale);
  factory Fixed.ratio(BigInt numerator, BigInt denominator) {
    if (denominator <= BigInt.zero) {
      throw ArgumentError.value(denominator, 'denominator', 'must be positive');
    }
    return Fixed.raw(numerator * scale ~/ denominator);
  }

  Fixed operator +(Fixed other) => Fixed.raw(raw + other.raw);
  Fixed operator -(Fixed other) => Fixed.raw(raw - other.raw);
  Fixed operator *(Fixed other) => Fixed.raw(raw * other.raw ~/ scale);
  Fixed operator /(Fixed other) {
    if (other.raw <= BigInt.zero)
      throw ArgumentError('positive divisor required');
    return Fixed.raw(raw * scale ~/ other.raw);
  }

  @override
  int compareTo(Fixed other) => raw.compareTo(other.raw);

  String toDecimalString({int decimals = 2}) {
    if (decimals < 0 || decimals > 24) throw RangeError.range(decimals, 0, 24);
    final absolute = raw.abs();
    final integer = absolute ~/ scale;
    if (decimals == 0) return '${raw.isNegative ? '-' : ''}$integer';
    final fractional = (absolute % scale).toString().padLeft(24, '0');
    return '${raw.isNegative ? '-' : ''}$integer.${fractional.substring(0, decimals)}';
  }

  @override
  String toString() => toDecimalString(decimals: 24);
}

/// Exact integer floor root. No floating-point estimate affects entitlement.
BigInt integerRoot(BigInt value, int degree) {
  if (value.isNegative || degree < 1)
    throw ArgumentError('nonnegative value and positive degree required');
  if (value <= BigInt.one || degree == 1) return value;
  var estimate = BigInt.one << ((value.bitLength + degree - 1) ~/ degree);
  final degreeBig = BigInt.from(degree);
  while (true) {
    final next = (BigInt.from(degree - 1) * estimate +
            value ~/ estimate.pow(degree - 1)) ~/
        degreeBig;
    if (next >= estimate) break;
    estimate = next;
  }
  while (estimate.pow(degree) > value) {
    estimate -= BigInt.one;
  }
  while ((estimate + BigInt.one).pow(degree) <= value) {
    estimate += BigInt.one;
  }
  return estimate;
}

BigInt ceilDivide(BigInt numerator, BigInt denominator) {
  if (numerator.isNegative || denominator <= BigInt.zero)
    throw ArgumentError(
        'ceilDivide requires nonnegative numerator and positive divisor');
  return (numerator + denominator - BigInt.one) ~/ denominator;
}

/// Natural log of x in [1,2], using 2*atanh((x-1)/(x+1)). Each
/// nonnegative operation truncates at 24 decimals. No platform math library.
BigInt _lnNormalized(BigInt x) {
  final z = (x - Fixed.scale) * Fixed.scale ~/ (x + Fixed.scale);
  final zSquared = z * z ~/ Fixed.scale;
  var term = z;
  var sum = BigInt.zero;
  var divisor = 1;
  while (term > BigInt.zero) {
    sum += term ~/ BigInt.from(divisor);
    term = term * zSquared ~/ Fixed.scale;
    divisor += 2;
  }
  return sum * BigInt.two;
}

final BigInt _lnTwo = _lnNormalized(Fixed.scale * BigInt.two);

/// log2(numerator/denominator) for ratios >= 1, including very large integers.
Fixed log2Ratio(BigInt numerator, BigInt denominator) {
  if (denominator <= BigInt.zero || numerator < denominator) {
    throw ArgumentError('log2Ratio requires numerator >= denominator > 0');
  }
  var exponent = numerator.bitLength - denominator.bitLength;
  if (numerator < (denominator << exponent)) exponent--;
  final normalized = numerator * Fixed.scale ~/ (denominator << exponent);
  return Fixed.raw(BigInt.from(exponent) * Fixed.scale +
      _lnNormalized(normalized) * Fixed.scale ~/ _lnTwo);
}

String formatMicros(BigInt value, {int decimals = 2}) {
  if (decimals < 0 || decimals > 6) throw RangeError.range(decimals, 0, 6);
  final sign = value.isNegative ? '-' : '';
  final absolute = value.abs();
  final whole = absolute ~/ BigInt.from(1000000);
  if (decimals == 0) return '$sign$whole';
  final fraction = (absolute % BigInt.from(1000000)).toString().padLeft(6, '0');
  return '$sign$whole.${fraction.substring(0, decimals)}';
}
