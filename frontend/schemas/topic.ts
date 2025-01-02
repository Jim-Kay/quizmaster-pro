import { z } from 'zod';

// Custom date validator that accepts ISO strings and converts them
const dateStringSchema = z.string().transform((val, ctx) => {
  try {
    const date = new Date(val);
    if (isNaN(date.getTime())) {
      ctx.addIssue({
        code: z.ZodIssueCode.invalid_date,
        message: 'Invalid date format',
      });
      return z.NEVER;
    }
    return date.toISOString();
  } catch {
    ctx.addIssue({
      code: z.ZodIssueCode.invalid_date,
      message: 'Invalid date format',
    });
    return z.NEVER;
  }
});

export const topicSchema = z.object({
  title: z.string()
    .min(3, 'Title must be at least 3 characters')
    .max(200, 'Title must be less than 200 characters'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters'),
});

export const topicResponseSchema = topicSchema.extend({
  topic_id: z.string(),
  created_at: dateStringSchema,
  updated_at: dateStringSchema,
});

export type TopicFormData = z.infer<typeof topicSchema>;

export interface Topic {
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}
