'use client'

import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

const objectiveSchema = z.object({
  id: z.string().uuid().optional(),
  title: z.string()
    .min(3, 'Title must be at least 3 characters')
    .max(200, 'Title must be less than 200 characters'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters'),
  type: z.enum(['terminal', 'enabling']),
  parentId: z.string().uuid().optional(),
});

const blueprintSchema = z.object({
  title: z.string()
    .min(3, 'Title must be at least 3 characters')
    .max(200, 'Title must be less than 200 characters'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters'),
  objectives: z.array(objectiveSchema)
    .min(1, 'At least one objective is required'),
});

type BlueprintFormData = z.infer<typeof blueprintSchema>;

interface CreateBlueprintFormProps {
  topicId: string;
}

export function CreateBlueprintForm({ topicId }: CreateBlueprintFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<BlueprintFormData>({
    resolver: zodResolver(blueprintSchema),
    defaultValues: {
      objectives: [{ title: '', description: '', type: 'terminal' }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'objectives',
  });

  const objectives = watch('objectives');
  const terminalObjectives = objectives?.filter(obj => obj.type === 'terminal') || [];

  const createBlueprint = useMutation({
    mutationFn: async (data: BlueprintFormData) => {
      const response = await fetch(`/api/topics/${topicId}/blueprints`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create blueprint');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints', topicId] });
      router.push(`/topics/${topicId}`);
    },
    onError: (error: Error) => {
      console.error('Failed to create blueprint:', error);
      // You could add a toast notification here
    },
  });

  const onSubmit = async (data: BlueprintFormData) => {
    try {
      await createBlueprint.mutateAsync(data);
    } catch (error) {
      console.error('Failed to create blueprint:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="space-y-6">
        <div>
          <label
            htmlFor="title"
            className="block text-sm font-medium text-gray-700"
          >
            Title
          </label>
          <input
            type="text"
            id="title"
            {...register('title')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700"
          >
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            {...register('description')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">
              {errors.description.message}
            </p>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Objectives</h3>
        <div className="space-y-6">
          {fields.map((field, index) => (
            <div
              key={field.id}
              className="p-4 border rounded-lg bg-gray-50 space-y-4"
            >
              <div className="flex justify-between items-center">
                <h4 className="text-sm font-medium text-gray-700">
                  Objective {index + 1}
                </h4>
                {fields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Type
                </label>
                <select
                  {...register(`objectives.${index}.type`)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="terminal">Terminal Objective</option>
                  <option value="enabling">Enabling Objective</option>
                </select>
              </div>

              {watch(`objectives.${index}.type`) === 'enabling' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Supports Terminal Objective
                  </label>
                  <select
                    {...register(`objectives.${index}.parentId`)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="">Select a terminal objective</option>
                    {terminalObjectives.map((obj, tIndex) => (
                      <option key={tIndex} value={obj.id}>
                        {obj.title || `Terminal Objective ${tIndex + 1}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Title
                </label>
                <input
                  type="text"
                  {...register(`objectives.${index}.title`)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
                {errors.objectives?.[index]?.title && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.objectives[index]?.title?.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  rows={3}
                  {...register(`objectives.${index}.description`)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
                {errors.objectives?.[index]?.description && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.objectives[index]?.description?.message}
                  </p>
                )}
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={() => append({ title: '', description: '', type: 'terminal' })}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Objective
          </button>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => router.back()}
          className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={createBlueprint.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {createBlueprint.isPending ? 'Creating...' : 'Create Blueprint'}
        </button>
      </div>

      {createBlueprint.isError && (
        <div className="mt-4 p-2 text-sm text-red-600 bg-red-50 rounded">
          Failed to create blueprint. Please try again.
        </div>
      )}
    </form>
  );
}
