import type { Category } from '../domain/mapObject';

interface Props {
  categories: Category[];
  visibleIds: string[];
  onChange: (ids: string[]) => void;
}

export function CategoryPanel({ categories, visibleIds, onChange }: Props) {
  return <details className="category-panel" open>
    <summary>Категории</summary>
    <button onClick={() => onChange(categories.map((category) => category.id))}>Показать все</button>
    {categories.map((category) => <label key={category.id}>
      <input type="checkbox" checked={visibleIds.includes(category.id)} onChange={() => onChange(
        visibleIds.includes(category.id) ? visibleIds.filter((id) => id !== category.id) : [...visibleIds, category.id],
      )} />
      <span aria-hidden="true" style={{ color: category.color }}>●</span>{category.name}
    </label>)}
  </details>;
}
