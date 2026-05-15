import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/utils/fabric_parser.dart';

void main() {
  test('parses leading percent syntax', () {
    final result = FabricParser.parse('%80 Cotton %20 Polyester');
    expect(result['cotton'], 80);
    expect(result['polyester'], 20);
  });

  test('parses trailing percent syntax with Turkish words', () {
    final result = FabricParser.parse('80% Pamuk 20% Polyester');
    expect(result['cotton'], 80);
    expect(result['polyester'], 20);
  });

  test('parses line separated entries', () {
    final result = FabricParser.parse('Pamuk 55\nPolyester 45');
    expect(result['cotton'], 55);
    expect(result['polyester'], 45);
  });

  test('keeps dynamic fabrics such as polyamide', () {
    final result = FabricParser.parse('%84 Viskon %16 Polyamid');
    expect(result['viscose'], 84);
    expect(result['polyamide'], 16);
  });

  test('parses Zara screenshot wording', () {
    final result = FabricParser.parse('57% viskoz\n31% poliamit\n12% keten');
    expect(result['viscose'], 57);
    expect(result['polyamide'], 31);
    expect(result['linen'], 12);
  });

  test('normalizes inflected fabric names', () {
    expect(FabricParser.normalizeFabricKey('viskozu'), 'viscose');
    expect(FabricParser.normalizeFabricKey('poliamidi'), 'polyamide');
  });

  test('keeps multi word fabrics', () {
    final result = FabricParser.parse('%95 Organic Cotton %5 Elastane');
    expect(result['organic cotton'], 95);
    expect(result['elastane'], 5);
  });
}
