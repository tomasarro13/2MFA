/// Puerto para la primitiva criptográfica HMAC-SHA1.
///
/// El dominio implementa TOTP desde cero; solo delega el hash a una librería
/// estándar (permitido por el laboratorio) a través de esta abstracción.
abstract interface class MacAlgorithm {
  List<int> sign(List<int> key, List<int> message);
}
