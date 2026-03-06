/**
 * ML Error Translator - User-friendly error messages for ML operations.
 *
 * Translates HTTP status codes and technical backend messages
 * into readable French messages for the end user.
 *
 * @module services/mlErrors
 */

/**
 * Known error patterns mapped to French user-friendly messages.
 * Keys are substrings matched against the raw error message (case-insensitive).
 */
const ML_ERROR_PATTERNS = {
    'microns-per-pixel': 'Cette lame n\'a pas de metadonnees de resolution (MPP). L\'analyse IA ne peut pas determiner l\'echelle.',
    'missing_mpp': 'Cette lame n\'a pas de metadonnees de resolution (MPP).',
    'mpp': 'Probleme de resolution de la lame (MPP manquant ou invalide).',
    'out of memory': 'Memoire insuffisante pour analyser cette lame. Essayez avec une resolution plus basse.',
    'oom': 'Memoire insuffisante pour analyser cette lame.',
    'cuda out of memory': 'Memoire GPU insuffisante. Le serveur est surcharge.',
    'model not loaded': 'Le modele IA n\'est pas charge. Contactez l\'administrateur.',
    'no model loaded': 'Aucun modele IA n\'est charge. Contactez l\'administrateur.',
    'slide not found': 'Lame introuvable. Verifiez que le fichier existe.',
    'not supported for ml': 'Ce format de lame n\'est pas supporte pour l\'analyse IA.',
    'ml features disabled': 'Les fonctionnalites IA sont desactivees dans la configuration.',
    'provider unavailable': 'Le moteur d\'analyse IA n\'est pas disponible.',
};

/**
 * HTTP status code to French message mapping.
 */
const HTTP_STATUS_MESSAGES = {
    429: "Le moteur d'inference est occupe. Reessayez dans quelques secondes.",
    503: "Le service d'analyse IA n'est pas disponible actuellement.",
    504: "L'analyse a pris trop de temps. Le serveur est peut-etre surcharge (CPU). Reessayez plus tard.",
    400: 'Requete invalide. Verifiez les parametres.',
    404: 'Lame introuvable.',
    422: 'Parametres invalides.',
};

/**
 * Translate a raw ML error into a user-friendly French message.
 *
 * @param {Error|string} error - The error object or message string
 * @returns {string} User-friendly message in French
 */
export function userFriendlyMLError(error) {
    // Extract message and status from error object
    const message = typeof error === 'string' ? error : (error.message || String(error));
    const status = error?.status || 0;

    // Check HTTP status first (most specific)
    if (status && HTTP_STATUS_MESSAGES[status]) {
        return HTTP_STATUS_MESSAGES[status];
    }

    // Check known patterns in the error message
    const messageLower = message.toLowerCase();
    for (const [pattern, friendlyMessage] of Object.entries(ML_ERROR_PATTERNS)) {
        if (messageLower.includes(pattern.toLowerCase())) {
            return friendlyMessage;
        }
    }

    // Network errors
    if (status === 0 || messageLower.includes('network error') || messageLower.includes('fetch')) {
        return 'Connexion au serveur impossible. Verifiez votre connexion reseau.';
    }

    // Generic server error
    if (status >= 500) {
        return 'Le serveur a rencontre un probleme. Reessayez dans quelques instants.';
    }

    // Fallback: return a sanitized version (no stack traces, no "Erreur" prefix)
    const sanitized = message.split('\n')[0].substring(0, 200);
    return sanitized;
}
