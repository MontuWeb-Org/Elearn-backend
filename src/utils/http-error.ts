export class HttpError extends Error {
  readonly statusCode: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(
    statusCode: number,
    message: string,
    options?: { code?: string; details?: unknown },
  ) {
    super(message);
    this.name = 'HttpError';
    this.statusCode = statusCode;
    this.code = options?.code ?? HttpError.defaultCode(statusCode);
    if (options?.details !== undefined) {
      this.details = options.details;
    }
    Error.captureStackTrace(this, HttpError);
  }

  private static defaultCode(statusCode: number): string {
    switch (statusCode) {
      case 400:
        return 'VALIDATION_ERROR';
      case 401:
        return 'UNAUTHENTICATED';
      case 403:
        return 'INSUFFICIENT_SCOPE';
      case 404:
        return 'NOT_FOUND';
      case 409:
        return 'CONFLICT';
      case 410:
        return 'GONE';
      case 422:
        return 'UNPROCESSABLE';
      default:
        return 'INTERNAL_ERROR';
    }
  }

  static badRequest(message = 'Bad Request', details?: unknown): HttpError {
    return new HttpError(400, message, { details });
  }

  static unauthorized(message = 'Unauthorized', code = 'UNAUTHENTICATED'): HttpError {
    return new HttpError(401, message, { code });
  }

  static forbidden(message = 'Forbidden', code = 'INSUFFICIENT_SCOPE'): HttpError {
    return new HttpError(403, message, { code });
  }

  static notFound(message = 'Not Found'): HttpError {
    return new HttpError(404, message, { code: 'NOT_FOUND' });
  }

  static conflict(message = 'Conflict', code = 'CONFLICT', details?: unknown): HttpError {
    return new HttpError(409, message, { code, details });
  }

  static gone(message = 'Gone', code = 'GONE'): HttpError {
    return new HttpError(410, message, { code });
  }

  static unprocessable(message = 'Unprocessable Entity', code = 'UNPROCESSABLE', details?: unknown): HttpError {
    return new HttpError(422, message, { code, details });
  }

  static internal(message = 'Internal Server Error'): HttpError {
    return new HttpError(500, message, { code: 'INTERNAL_ERROR' });
  }
}
