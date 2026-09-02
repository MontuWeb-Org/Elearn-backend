export class HttpError extends Error {
  readonly statusCode: number;
  readonly details?: unknown;

  constructor(statusCode: number, message: string, details?: unknown) {
    super(message);
    this.name = 'HttpError';
    this.statusCode = statusCode;
    if (details !== undefined) {
      this.details = details;
    }
    Error.captureStackTrace(this, HttpError);
  }

  static badRequest(message = 'Bad Request', details?: unknown): HttpError {
    return new HttpError(400, message, details);
  }

  static unauthorized(message = 'Unauthorized'): HttpError {
    return new HttpError(401, message);
  }

  static forbidden(message = 'Forbidden'): HttpError {
    return new HttpError(403, message);
  }

  static notFound(message = 'Not Found'): HttpError {
    return new HttpError(404, message);
  }

  static internal(message = 'Internal Server Error'): HttpError {
    return new HttpError(500, message);
  }
}
