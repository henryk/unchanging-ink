/**
 * Validate a timestamp input
 *
 * @param ts Timestamp input, as a string or an object
 * @returns {Object} The validated timestamp object
 * @throws {Error} If the input is not a valid timestamp object
 */
export async function validateTsInput(ts) {
  // Type check
  if (typeof ts !== 'string' && typeof ts !== 'object') {
    throw new Error('Invalid timestamp: input must be a string or an object');
  }

  const requiredFields = ['timestamp', 'typ', 'version', 'interval', 'proof', 'hash', 'id'];
  hasRequiredFields(ts, requiredFields, 'timestamp');

  // check typ
  if (ts.typ !== 'ts') {
    throw new Error('Invalid timestamp: typ field must be "ts"');
  }

  // check hash must be base64
  if (!('hash' in ts) || !isBase64Str(ts.hash)) {
    throw new Error('Invalid timestamp: hash field must be a base64 string');
  }

  //  check version to be valid
  if (ts.version !== '1') {
    throw new Error('Invalid timestamp: version field must be "1"');
  }

  // check timestamp is ISO 8601 date string (UTC)
  if (
    typeof ts.timestamp !== 'string' ||
    !ts.timestamp.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/)
  ) {
    throw new Error(
      'Invalid timestamp: timestamp field must be an ISO 8601 date string'
    );
  }

  // check interval is non-negative integer
  if (!isNonNegativeInteger(ts.interval)) {
    throw new Error('Invalid timestamp: interval field must be a non-negative integer');
  }

  // check id is a valid UUID
  if (typeof ts.id !== 'string' || !ts.id.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)) {
    throw new Error('Invalid timestamp: id field must be a valid UUID string');
  }

  // chek proof is a valid proof object
  if (!validateProof(ts.proof)) {
    throw new Error('Invalid timestamp: proof field is not valid');
  }

  // return ts if checks passed
  return ts;
}

/**
 * Validate a timestamp proof object
 *
 * @param proof Object representing a timestamp proof, as returned by the server
 * @returns {boolean} True, if proof is valid
 */
function validateProof(proof) {
  const requiredFields = ['a', 'path', 'ith', 'mth'];
  hasRequiredFields(proof, requiredFields, 'proof');

  // a must be non-negative integer, not array
  if (Array.isArray(proof.a)) {
    throw new Error('Invalid proof: field a must NOT be an array');
  }
  if (typeof proof.a !== 'number' || !isNonNegativeInteger(proof.a)) {
    throw new Error('Invalid proof: field a must be a non-negative integer');
  }

  // path = array of base64 strings
  if (!Array.isArray(proof.path)) {
    throw new Error('Invalid proof: field path must be an array');
  }
  for (const element of proof.path) {
    if (!isBase64Str(element)) {
      throw new Error('Invalid proof: field path must be an array of base64 strings');
    }
  }

  // ith must be base64
  if (!isBase64Str(proof.ith)) {
    throw new Error('Invalid proof: field ith must be a base64 string');
  }

  // mth format check
  validateMth(proof.mth);

  return true;
}

/**
 * Check if an object has all required fields
 *
 * @param obj Object to check
 * @param fields Array of required fields
 * @param name Name of the object for error messages, defaults to 'Object'
 */
function hasRequiredFields(obj, fields, name = 'Object') {
  for (const field of fields) {
    if (!(field in obj)) {
      throw new Error(`Invalid ${name}: missing required field ${field}`);
    }
  }
}

/**
 * Determines whether a given string is a valid Base64 encoded string.
 *
 * @param {string} str - The string to check for Base64 encoding validity.
 * @return {boolean} - Returns true if the string is a valid Base64 encoded string, false otherwise.
 */
function isBase64Str(str) {
  if (typeof str !== 'string' || str.length === 0) return false
  if (!/^[A-Za-z0-9+/]+={0,2}$/.test(str)) return false
  // Länge darf mod 4 nicht 1 sein (ungültiges Base64)
  return str.length % 4 !== 1
}

/**
 * Checks whether the given string is a valid Base64 URL-encoded string.
 *
 * @param {string} str - The string to be checked.
 * @return {boolean} Returns true if the string is a valid Base64 URL-encoded string, otherwise false.
 */
function isBase64UrlStr(str) {
  if (typeof str !== 'string' || str.length === 0) return false
  if (!/^[A-Za-z0-9_-]+={0,2}$/.test(str)) return false
  return str.length % 4 !== 1
}

/**
 * Checks if the provided value is a non-negative integer.
 *
 * @param {*} n - The value to be checked.
 * @return {boolean} Returns true if the value is a non-negative integer, otherwise false.
 */
function isNonNegativeInteger(n) {
  return Number.isSafeInteger(n) && n >= 0;
}

/**
 * Validates the given merkle tree head string to ensure it adheres to the required format and rules.
 *
 * @param {string} mthStr The mth string to validate. It must be a string following the specific pattern: authority/i#v1:mth.
 * @return {void} Throws an error if the mth string is invalid or does not meet the specified requirements.
 */
function validateMth(mthStr) {
  if (typeof mthStr !== 'string') {
    throw new Error('Invalid proof: field mth must be a string');
  }

  let authority, rest;
  if (mthStr.startsWith('http://') || mthStr.startsWith('https://')) {
    const schemePos = mthStr.indexOf('//');
    const thirdSlash = mthStr.indexOf('/', schemePos + 2);
    if (thirdSlash === -1) {
      throw new Error('Invalid proof: field mth must contain /i after authority');
    }
    authority = mthStr.slice(0, thirdSlash); // includes scheme
    rest = mthStr.slice(thirdSlash);         // starts with /i#...
  } else {
    const firstSlash = mthStr.indexOf('/');
    if (firstSlash === -1) {
      throw new Error('Invalid proof: field mth must contain /i after authority');
    }
    authority = mthStr.slice(0, firstSlash); // host[:port]
    rest = mthStr.slice(firstSlash);         // starts with /i#...
  }

  const authorityPattern =
    /^(?:(?:https?:\/\/))?(?:localhost|[A-Z0-9-]+(?:\.[A-Z0-9-]+)*|\d{1,3}(?:\.\d{1,3}){3})(?::\d{1,5})?$/i;
  if (!authorityPattern.test(authority)) {
    throw new Error('Invalid proof: invalid authority in mth');
  }

  // Expect /<i>#v1:<mth>
  const match = rest.match(/^\/(\d+)#(v1):([A-Za-z0-9_-]+={0,2})$/);
  if (!match) {
    throw new Error('Invalid proof: field mth must match authority/i#v1:mth');
  }

  const iStr = match[1];
  const mthHash = match[3];

  if (!/^\d+$/.test(iStr)) {
    throw new Error('Invalid proof: i in mth must be a base-10 integer');
  }
  const iVal = Number(iStr);
  if (!Number.isSafeInteger(iVal) || iVal < 0) {
    throw new Error('Invalid proof: i in mth must be a non-negative integer');
  }

  if (!isBase64UrlStr(mthHash)) {
    throw new Error('Invalid proof: mth must be a base64url string');
  }
}
